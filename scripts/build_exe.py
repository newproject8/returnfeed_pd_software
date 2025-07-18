#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 빌드 스크립트
PyInstaller를 사용하여 실행 파일 생성
"""

import os
import sys
import shutil
import PyInstaller.__main__

# 프로젝트 정보
APP_NAME = "PD_Software"
VERSION = "1.0.0"
AUTHOR = "ReturnFeed"
DESCRIPTION = "PD 통합 소프트웨어 - NDI, vMix Tally, SRT Streaming"

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(BASE_DIR, "main_integrated.py")
BUILD_DIR = os.path.join(BASE_DIR, "build")
DIST_DIR = os.path.join(BASE_DIR, "dist")
SPEC_DIR = os.path.join(BASE_DIR, "specs")

# NDI DLL 경로 (Windows)
NDI_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"

def clean_build():
    """이전 빌드 정리"""
    print("이전 빌드 정리 중...")
    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"  - {dir_path} 삭제됨")

def create_spec_file():
    """PyInstaller spec 파일 생성"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# 추가 데이터 파일
added_files = [
    ('pd_app', 'pd_app'),
    ('config', 'config'),
]

# 바이너리 파일 (NDI DLL 포함)
binaries = []
if sys.platform == "win32":
    ndi_dll_path = r"{NDI_DLL_PATH}"
    if os.path.exists(ndi_dll_path):
        binaries.append((ndi_dll_path + '\\\\*.dll', '.'))

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=['{BASE_DIR}'],
    binaries=binaries,
    datas=added_files,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'numpy',
        'cv2',
        'pyqtgraph',
        'websockets',
        'ffmpeg',
        'NDIlib',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version.txt',
    uac_admin=False,  # 관리자 권한 불필요
    icon=None,  # 아이콘 파일이 있으면 여기에 경로 지정
)
'''
    
    # specs 디렉토리 생성
    os.makedirs(SPEC_DIR, exist_ok=True)
    spec_file = os.path.join(SPEC_DIR, f"{APP_NAME}.spec")
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"Spec 파일 생성됨: {spec_file}")
    return spec_file

def create_version_file():
    """Windows 버전 정보 파일 생성"""
    version_content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{AUTHOR}'),
        StringStruct(u'FileDescription', u'{DESCRIPTION}'),
        StringStruct(u'FileVersion', u'{VERSION}'),
        StringStruct(u'InternalName', u'{APP_NAME}'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024 {AUTHOR}'),
        StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
        StringStruct(u'ProductName', u'{APP_NAME}'),
        StringStruct(u'ProductVersion', u'{VERSION}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    
    version_file = os.path.join(BASE_DIR, "version.txt")
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version_content)
    
    print(f"버전 정보 파일 생성됨: {version_file}")
    return version_file

def build_executable():
    """실행 파일 빌드"""
    print(f"\n{APP_NAME} v{VERSION} 빌드 시작...")
    
    # 1. 이전 빌드 정리
    clean_build()
    
    # 2. 버전 정보 파일 생성 (Windows)
    if sys.platform == "win32":
        create_version_file()
    
    # 3. Spec 파일 생성
    spec_file = create_spec_file()
    
    # 4. PyInstaller 실행
    print("\nPyInstaller 실행 중...")
    args = [
        spec_file,
        '--clean',
        '--noconfirm',
        f'--distpath={DIST_DIR}',
        f'--workpath={BUILD_DIR}',
    ]
    
    try:
        PyInstaller.__main__.run(args)
        print(f"\n빌드 완료! 실행 파일: {os.path.join(DIST_DIR, APP_NAME)}")
        
        # 5. 추가 파일 복사
        copy_additional_files()
        
    except Exception as e:
        print(f"\n빌드 실패: {e}")
        return False
    
    return True

def copy_additional_files():
    """추가 파일 복사"""
    print("\n추가 파일 복사 중...")
    
    # README 파일
    readme_files = [
        "README.md",
        "통합_프로젝트_계획서.md",
        "디버깅_보고서.md"
    ]
    
    for readme in readme_files:
        src = os.path.join(BASE_DIR, readme)
        if os.path.exists(src):
            dst = os.path.join(DIST_DIR, readme)
            shutil.copy2(src, dst)
            print(f"  - {readme} 복사됨")
    
    # requirements.txt
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.exists(req_file):
        shutil.copy2(req_file, os.path.join(DIST_DIR, "requirements.txt"))
        print("  - requirements.txt 복사됨")

def create_installer_script():
    """간단한 설치 스크립트 생성"""
    installer_content = """@echo off
echo PD 통합 소프트웨어 설치
echo ======================
echo.

echo 1. 필수 구성 요소 확인 중...
echo    - Python 3.9+ (설치됨)
echo    - NDI SDK (선택사항)
echo    - FFmpeg (SRT 스트리밍용)
echo.

echo 2. 프로그램 파일 복사 중...
xcopy /E /I /Y "%~dp0*" "%PROGRAMFILES%\\PD_Software\\"

echo 3. 바탕화면 바로가기 생성 중...
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\\Desktop\\PD Software.lnk');$s.TargetPath='%PROGRAMFILES%\\PD_Software\\PD_Software.exe';$s.Save()"

echo.
echo 설치 완료!
echo PD Software가 성공적으로 설치되었습니다.
echo.
pause
"""
    
    installer_file = os.path.join(DIST_DIR, "install.bat")
    with open(installer_file, 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    print(f"설치 스크립트 생성됨: {installer_file}")

def main():
    """메인 빌드 프로세스"""
    print("=" * 60)
    print(f"{APP_NAME} 빌드 스크립트")
    print("=" * 60)
    
    # PyInstaller 설치 확인
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller가 설치되지 않았습니다.")
        print("설치: pip install pyinstaller")
        return
    
    # 빌드 실행
    if build_executable():
        # Windows용 설치 스크립트 생성
        if sys.platform == "win32":
            create_installer_script()
        
        print("\n빌드 성공!")
        print(f"실행 파일 위치: {DIST_DIR}")
        print("\n배포 준비:")
        print("1. dist 폴더의 모든 파일을 압축")
        print("2. 사용자에게 배포")
        print("3. install.bat 실행하여 설치 (Windows)")
    else:
        print("\n빌드 실패!")

if __name__ == "__main__":
    main()