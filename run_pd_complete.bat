@echo off
REM PD 통합 소프트웨어 완전 실행 배치 파일
REM 모든 설정 자동화

REM 콘솔 UTF-8 설정
chcp 65001 > nul 2>&1

REM 환경 변수 설정
set QT_ENABLE_HIGHDPI_SCALING=1
set QT_AUTO_SCREEN_SCALE_FACTOR=1
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
set PYTHONIOENCODING=utf-8

REM 타이틀 설정
title PD 통합 소프트웨어 v1.0.0

REM Python 실행
python run_pd_complete.py

REM 종료 시 일시 정지
pause