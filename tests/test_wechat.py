import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_wechat_verify():
    """测试企业微信 URL 验证"""
    response = client.get("/wechat/callback", params={
        "msg_signature": "test",
        "timestamp": "1234567890",
        "nonce": "test",
        "echostr": "test_echostr"
    })
    assert response.status_code == 200
