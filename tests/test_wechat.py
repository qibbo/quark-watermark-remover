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

def test_parse_file_message():
    """测试解析文件消息"""
    xml_data = """
    <xml>
        <ToUserName><![CDATA[wxid_test]]></ToUserName>
        <FromUserName><![CDATA[user_test]]></FromUserName>
        <CreateTime>1234567890</CreateTime>
        <MsgType><![CDATA[file]]></MsgType>
        <MediaId><![CDATA[media_id_test]]></MediaId>
        <FileName><![CDATA[test.pdf]]></FileName>
        <FileSize>12345</FileSize>
    </xml>
    """
    from app.wechat import parse_file_message
    result = parse_file_message(xml_data)
    assert result["media_id"] == "media_id_test"
    assert result["file_name"] == "test.pdf"
    assert result["from_user"] == "user_test"
