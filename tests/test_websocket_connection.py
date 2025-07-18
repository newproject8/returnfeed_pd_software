#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 연결 테스트 스크립트
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """WebSocket 연결 테스트"""
    urls_to_test = [
        "ws://returnfeed.net:8765",
        "ws://returnfeed.net:8766",
        "ws://returnfeed.net:80",
        "ws://returnfeed.net/ws",
        "wss://returnfeed.net:8765",
        "wss://returnfeed.net/ws"
    ]
    
    for url in urls_to_test:
        logger.info(f"\n테스트 중: {url}")
        try:
            async with websockets.connect(url, timeout=5) as websocket:
                logger.info(f"✓ 연결 성공: {url}")
                
                # 테스트 메시지 전송
                test_message = {"type": "ping", "timestamp": 1234567890}
                await websocket.send(json.dumps(test_message))
                logger.info(f"메시지 전송: {test_message}")
                
                # 응답 대기 (1초)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1)
                    logger.info(f"응답 수신: {response}")
                except asyncio.TimeoutError:
                    logger.warning("응답 타임아웃 (1초)")
                    
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"✗ HTTP 상태 코드 오류: {e}")
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"✗ WebSocket 오류: {e}")
        except asyncio.TimeoutError:
            logger.error(f"✗ 연결 타임아웃 (5초)")
        except Exception as e:
            logger.error(f"✗ 기타 오류: {type(e).__name__}: {e}")

async def test_http_endpoints():
    """HTTP 엔드포인트 테스트"""
    import aiohttp
    
    endpoints = [
        "http://returnfeed.net:8765",
        "http://returnfeed.net:8766",
        "http://returnfeed.net/api/status"
    ]
    
    logger.info("\n\nHTTP 엔드포인트 테스트:")
    
    async with aiohttp.ClientSession() as session:
        for url in endpoints:
            try:
                async with session.get(url, timeout=5) as response:
                    logger.info(f"{url} - 상태: {response.status}")
                    if response.status == 200:
                        text = await response.text()
                        logger.info(f"응답 내용: {text[:100]}...")
            except Exception as e:
                logger.error(f"{url} - 오류: {e}")

async def main():
    """메인 테스트 함수"""
    logger.info("WebSocket 연결 테스트 시작")
    
    await test_websocket_connection()
    
    try:
        await test_http_endpoints()
    except ImportError:
        logger.warning("aiohttp가 설치되지 않아 HTTP 테스트 건너뜀")

if __name__ == "__main__":
    asyncio.run(main())