#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path
from PIL import Image
import tkinter as tk
from tkinter import filedialog

if sys.platform == 'win32':
    import msvcrt
else:
    import tty
    import termios


MAX_BAR_LENGTH = 40
MIN_QUALITY_RANGE = 50
MAX_QUALITY_RANGE = 100
DEFAULT_QUALITY_MIN = 65
DEFAULT_QUALITY_MAX = 90
PNGQUANT_SPEED = 1


class KeyHandler:
    """Обрабочик клавиш"""
    
    @staticmethod
    def getKey():
        if sys.platform == 'win32':
            key = msvcrt.getch()
            if key == b'\xe0' or key == b'\x00':
                key = msvcrt.getch()
                if key == b'H':
                    return 'up'
                elif key == b'P':
                    return 'down'
            elif key == b'\r':
                return 'enter'
            elif key == b'\x1b':
                return 'esc'
            else:
                try:
                    return key.decode('utf-8')
                except:
                    return ''
        else:
            fd = sys.stdin.fileno()
            oldSettings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if ch3 == 'A':
                            return 'up'
                        elif ch3 == 'B':
                            return 'down'
                    return 'esc'
                elif ch == '\r' or ch == '\n':
                    return 'enter'
                else:
                    return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
        return ''


class Colors:
    """ANSI"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    REVERSE = '\033[7m'
    END = '\033[0m'


def clearScreen():
    os.system('cls' if sys.platform == 'win32' else 'clear')


def formatSize(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"


def printHeader():
    print(f"\n{Colors.BOLD}{Colors.BLUE}        🖼️  IMAGE COMPRESSOR  🖼️{Colors.END}")
    print(f"{Colors.CYAN}{'─' * 60}{Colors.END}")


def selectFile():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    filePath = filedialog.askopenfilename(
        title="Выберите изображение",
        filetypes=[
            ("Изображения", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("Все файлы", "*.*")
        ]
    )
    
    root.destroy()
    return filePath


def selectDirectory():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    dirPath = filedialog.askdirectory(title="Выберите папку с изображениями")
    
    root.destroy()
    return dirPath


def selectOutputDirectory():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    dirPath = filedialog.askdirectory(
        title="Выберите папку для сохранения (отмена = исходная папка)"
    )
    
    root.destroy()
    return dirPath if dirPath else None


def checkPngquant():
    try:
        subprocess.run(
            ['pngquant', '--version'], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, 
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def compressWithPngquant(inputPath, outputPath, qualityMin=65, qualityMax=90):
    try:
        cmd = [
            'pngquant',
            '--quality', f'{qualityMin}-{qualityMax}',
            '--speed', str(PNGQUANT_SPEED),
            '--strip',
            '--force',
            '--output', str(outputPath),
            str(inputPath)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"{Colors.RED}Ошибка pngquant: {e}{Colors.END}")
        return False


def compressWithPillow(inputPath, outputPath, quality=90):
    try:
        with Image.open(inputPath) as img:
            if outputPath.suffix.lower() in ['.jpg', '.jpeg']:
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                else:
                    img = img.convert('RGB')
                
                img.save(outputPath, 'JPEG', quality=quality, optimize=True)
            elif outputPath.suffix.lower() == '.webp':
                img.save(outputPath, 'WEBP', quality=quality, method=6)
            else:
                img.save(outputPath, 'PNG', optimize=True, compress_level=9)
        
        return True
    except Exception as e:
        print(f"{Colors.RED}Ошибка Pillow: {e}{Colors.END}")
        return False


def compressImageAdvanced(inputPath, outputDir=None, qualityMin=65, qualityMax=90, usePngquant=True):
    inputPath = Path(inputPath)
    
    if not inputPath.exists():
        return None
    
    if outputDir:
        outputDir = Path(outputDir)
        outputDir.mkdir(parents=True, exist_ok=True)
        outputPath = outputDir / inputPath.name
    else:
        outputPath = inputPath.parent / f"{inputPath.stem}_compressed{inputPath.suffix}"
    
    originalSize = os.path.getsize(inputPath)
    
    if usePngquant and inputPath.suffix.lower() == '.png' and checkPngquant():
        success = compressWithPngquant(inputPath, outputPath, qualityMin, qualityMax)
        if not success:
            compressWithPillow(inputPath, outputPath)
    else:
        compressWithPillow(inputPath, outputPath, quality=(qualityMin + qualityMax) // 2)
    
    if outputPath.exists():
        compressedSize = os.path.getsize(outputPath)
        savings = ((originalSize - compressedSize) / originalSize) * 100 if originalSize > 0 else 0
        return (originalSize, compressedSize, savings)
    
    return None


def drawMenu(options, selectedIdx, title="Меню"):
    clearScreen()
    printHeader()
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{title}{Colors.END}\n")
    
    for idx, option in enumerate(options):
        if idx == selectedIdx:
            print(f"  {Colors.REVERSE}{Colors.GREEN}❯ {option}{Colors.END}")
        else:
            print(f"  {Colors.DIM}  {option}{Colors.END}")
    
    print(f"\n{Colors.DIM}↑↓ навигация | Enter выбор | ESC выход{Colors.END}")


def showSettings(currentQualityMin, currentQualityMax, usePngquant):
    options = [
        f"Качество мин: {currentQualityMin}%",
        f"Качество макс: {currentQualityMax}%",
        f"Использовать pngquant: {'Да' if usePngquant else 'Нет'}",
        "Назад"
    ]
    
    selected = 0
    
    while True:
        clearScreen()
        printHeader()
        print(f"\n{Colors.BOLD}{Colors.YELLOW}⚙️  Настройки{Colors.END}\n")
        
        for idx, option in enumerate(options):
            if idx == selected:
                print(f"  {Colors.REVERSE}{Colors.GREEN}❯ {option}{Colors.END}")
            else:
                print(f"  {Colors.DIM}  {option}{Colors.END}")
        
        print(f"\n{Colors.DIM}Диапазон качества 65-90 = визуально lossless, ~70% экономии{Colors.END}")
        print(f"{Colors.DIM}Диапазон качества 80-95 = почти идеально, ~50% экономии{Colors.END}")
        print(f"\n{Colors.DIM}↑↓ навигация | Enter выбор | ESC назад{Colors.END}")
        
        key = KeyHandler.getKey()
        
        if key == 'up':
            selected = (selected - 1) % len(options)
        elif key == 'down':
            selected = (selected + 1) % len(options)
        elif key == 'enter':
            if selected == 0:
                clearScreen()
                printHeader()
                print(f"\n{Colors.YELLOW}Минимальное качество ({MIN_QUALITY_RANGE}-95): {Colors.END}", 
                      end='', flush=True)
                try:
                    val = int(input())
                    if MIN_QUALITY_RANGE <= val <= 95:
                        currentQualityMin = val
                        options[0] = f"Качество мин: {currentQualityMin}%"
                except:
                    pass
            elif selected == 1:
                clearScreen()
                printHeader()
                print(f"\n{Colors.YELLOW}Максимальное качество (60-{MAX_QUALITY_RANGE}): {Colors.END}", 
                      end='', flush=True)
                try:
                    val = int(input())
                    if 60 <= val <= MAX_QUALITY_RANGE:
                        currentQualityMax = val
                        options[1] = f"Качество макс: {currentQualityMax}%"
                except:
                    pass
            elif selected == 2:
                usePngquant = not usePngquant
                options[2] = f"Использовать pngquant: {'Да' if usePngquant else 'Нет'}"
            elif selected == 3:
                return currentQualityMin, currentQualityMax, usePngquant
        elif key == 'esc':
            return currentQualityMin, currentQualityMax, usePngquant


def compressSingleFile(qualityMin, qualityMax, usePngquant):
    clearScreen()
    printHeader()
    print(f"\n{Colors.YELLOW}📁 Выберите файл для сжатия{Colors.END}\n")
    
    filePath = selectFile()
    
    if not filePath:
        print(f"{Colors.RED}Файл не выбран{Colors.END}")
        input(f"\n{Colors.DIM}Нажмите Enter...{Colors.END}")
        return
    
    print(f"{Colors.GREEN}Выбран: {Path(filePath).name}{Colors.END}")
    print(f"\n{Colors.YELLOW}📂 Выберите папку для сохранения{Colors.END}")
    print(f"{Colors.DIM}(отмена = сохранить рядом с оригиналом){Colors.END}\n")
    
    outputDir = selectOutputDirectory()
    
    print(f"\n{Colors.YELLOW}⏳ Сжатие...{Colors.END}\n")
    
    result = compressImageAdvanced(filePath, outputDir, qualityMin, qualityMax, usePngquant)
    
    if result:
        originalSize, compressedSize, savings = result
        
        origBar = '█' * MAX_BAR_LENGTH
        compBar = '█' * int((compressedSize / originalSize) * MAX_BAR_LENGTH) if originalSize > 0 else ''
        
        print(f"{Colors.CYAN}{'─' * 60}{Colors.END}")
        print(f"   Оригинал:  {Colors.BLUE}{origBar}{Colors.END} {formatSize(originalSize)}")
        print(f"   Сжатый:    {Colors.GREEN}{compBar}{Colors.END} {formatSize(compressedSize)}")
        
        if savings > 0:
            print(f"\n   {Colors.GREEN}✅ Экономия: {savings:.1f}%{Colors.END}")
        elif savings < 0:
            print(f"\n   {Colors.YELLOW}⚠️  Увеличение: {abs(savings):.1f}%{Colors.END}")
        else:
            print(f"\n   {Colors.CYAN}ℹ️  Без изменений{Colors.END}")
        print(f"{Colors.CYAN}{'─' * 60}{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Ошибка сжатия{Colors.END}")
    
    input(f"\n{Colors.DIM}Нажмите Enter...{Colors.END}")


def compressDirectoryFiles(qualityMin, qualityMax, usePngquant):
    clearScreen()
    printHeader()
    print(f"\n{Colors.YELLOW}📂 Выберите папку с изображениями{Colors.END}\n")
    
    dirPath = selectDirectory()
    
    if not dirPath:
        print(f"{Colors.RED}Папка не выбрана{Colors.END}")
        input(f"\n{Colors.DIM}Нажмите Enter...{Colors.END}")
        return
    
    print(f"{Colors.GREEN}Выбрана: {dirPath}{Colors.END}")
    print(f"\n{Colors.YELLOW}📂 Выберите папку для сохранения{Colors.END}")
    print(f"{Colors.DIM}(отмена = сохранить в исходной папке){Colors.END}\n")
    
    outputDir = selectOutputDirectory()
    
    inputDir = Path(dirPath)
    extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
    
    imageFiles = []
    for ext in extensions:
        imageFiles.extend(inputDir.glob(f"*{ext}"))
        imageFiles.extend(inputDir.glob(f"*{ext.upper()}"))
    
    if not imageFiles:
        print(f"{Colors.RED}❌ Изображения не найдены{Colors.END}")
        input(f"\n{Colors.DIM}Нажмите Enter...{Colors.END}")
        return
    
    print(f"\n{Colors.GREEN}Найдено файлов: {len(imageFiles)}{Colors.END}")
    print(f"{Colors.YELLOW}⏳ Обработка...{Colors.END}\n")
    
    totalOriginal = 0
    totalCompressed = 0
    successCount = 0
    
    for idx, imgFile in enumerate(imageFiles, 1):
        print(f"[{idx}/{len(imageFiles)}] {imgFile.name}...", end=' ', flush=True)
        
        result = compressImageAdvanced(imgFile, outputDir, qualityMin, qualityMax, usePngquant)
        
        if result:
            orig, comp, _ = result
            totalOriginal += orig
            totalCompressed += comp
            successCount += 1
            print(f"{Colors.GREEN}✓{Colors.END}")
        else:
            print(f"{Colors.RED}✗{Colors.END}")
    
    if totalOriginal > 0:
        totalSavings = ((totalOriginal - totalCompressed) / totalOriginal) * 100
        
        print(f"\n{Colors.GREEN}{'═' * 60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}📊 ИТОГО{Colors.END}")
        print(f"{Colors.GREEN}{'═' * 60}{Colors.END}")
        print(f"\n   Обработано:  {Colors.BOLD}{successCount}{Colors.END}/{len(imageFiles)}")
        print(f"   Оригинал:    {Colors.BLUE}{formatSize(totalOriginal)}{Colors.END}")
        print(f"   Сжатый:      {Colors.GREEN}{formatSize(totalCompressed)}{Colors.END}")
        print(f"   Экономия:    {Colors.YELLOW}{formatSize(totalOriginal - totalCompressed)}{Colors.END} ({totalSavings:.1f}%)")
        print(f"\n{Colors.GREEN}{'═' * 60}{Colors.END}")
    
    input(f"\n{Colors.DIM}Нажмите Enter...{Colors.END}")


def main():
    if sys.platform == 'win32':
        os.system('color')
    
    settings = {
        'qualityMin': DEFAULT_QUALITY_MIN,
        'qualityMax': DEFAULT_QUALITY_MAX,
        'usePngquant': True
    }
    
    menuOptions = [
        "📁 Сжать один файл",
        "📂 Сжать папку",
        "⚙️  Настройки",
        "❌ Выход"
    ]
    
    selected = 0
    
    while True:
        drawMenu(menuOptions, selected, "Главное меню")
        
        key = KeyHandler.getKey()
        
        if key == 'up':
            selected = (selected - 1) % len(menuOptions)
        elif key == 'down':
            selected = (selected + 1) % len(menuOptions)
        elif key == 'enter' or key in ['1', '2', '3', '4']:
            if key in ['1', '2', '3', '4']:
                selected = int(key) - 1
            
            if selected == 0:
                compressSingleFile(
                    settings['qualityMin'],
                    settings['qualityMax'],
                    settings['usePngquant']
                )
            elif selected == 1:
                compressDirectoryFiles(
                    settings['qualityMin'],
                    settings['qualityMax'],
                    settings['usePngquant']
                )
            elif selected == 2:
                qMin, qMax, usePq = showSettings(
                    settings['qualityMin'],
                    settings['qualityMax'],
                    settings['usePngquant']
                )
                settings['qualityMin'] = qMin
                settings['qualityMax'] = qMax
                settings['usePngquant'] = usePq
            elif selected == 3:
                clearScreen()
                print(f"\n{Colors.CYAN}Спасибо за использование! 👋{Colors.END}\n")
                sys.exit(0)
        elif key == 'esc':
            clearScreen()
            print(f"\n{Colors.CYAN}Спасибо за использование! 👋{Colors.END}\n")
            sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        clearScreen()
        print(f"\n{Colors.YELLOW}Программа прервана пользователем{Colors.END}\n")
        sys.exit(0)