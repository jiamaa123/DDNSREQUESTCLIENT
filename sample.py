# coding=utf-8
import json
import os.path
import platform

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import dnspod_client, models

FILEPATH = "ipCheck"


def check(ipv6Address):
    ipv6Infile = ""
    if not os.path.exists(FILEPATH):
        with open(FILEPATH, "w") as f:
            f.write(ipv6Address)
    else:
        with open(FILEPATH, "r") as f:
            ipv6Infile = f.readline()

    if ipv6Infile == ipv6Address:
        ret = False
    else:
        ret = True
    return ret


def insertRecord(client, ipv6Address, hostname, domain):
    params = {
        "Domain": domain,
        "SubDomain": hostname,
        "RecordType": "AAAA",
        "RecordLine": "默认",
        "Value": ipv6Address,
    }
    createRecord(client, params)


def modifyRecordByRecordId(client, ipv6Address, recordId, hostname, domain):
    params = {
        "Domain": domain,
        "SubDomain": hostname,
        "RecordType": "AAAA",
        "RecordLine": "默认",
        "Value": ipv6Address,
        "RecordId": recordId
    }
    print(modifyRecordRequest(client, params))


def getRecordIdByHostName(client, hostname, domain):
    params = {
        "Domain": domain,
        "RecordType": ["AAAA"],
        "Keyword": hostname
    }
    recordIdDict = json.loads(describeRecordFilterList(client, params))
    return recordIdDict["RecordList"][0]["RecordId"] if len(recordIdDict["RecordList"]) > 0 else None


def createRecord(client, params):
    # 实例化一个请求对象,每个接口都会对应一个request对象
    req = models.CreateRecordRequest()
    req.from_json_string(json.dumps(params))
    # 返回的resp是一个ModifyRecordResponse的实例，与请求对象对应
    resp = client.CreateRecord(req)
    # 输出json格式的字符串回包
    return resp.to_json_string()


def modifyRecordRequest(client, params):
    # 实例化一个请求对象,每个接口都会对应一个request对象
    req = models.ModifyRecordRequest()
    req.from_json_string(json.dumps(params))
    # 返回的resp是一个ModifyRecordResponse的实例，与请求对象对应
    resp = client.ModifyRecord(req)
    # 输出json格式的字符串回包
    return resp.to_json_string()


def describeRecordFilterList(client, params):
    # 实例化一个请求对象,每个接口都会对应一个request对象
    req = models.DescribeRecordFilterListRequest()
    req.from_json_string(json.dumps(params))

    # 返回的resp是一个ModifyRecordResponse的实例，与请求对象对应
    resp = client.DescribeRecordFilterList(req)
    # 输出json格式的字符串回包
    return resp.to_json_string()


def getClient():
    ret = None
    try:
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(os.environ.get("TENCENTCLOUD_SECRET_ID"),
                                     os.getenv("TENCENTCLOUD_SECRET_KEY"))
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "dnspod.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        ret = dnspod_client.DnspodClient(cred, "", clientProfile)
    except TencentCloudSDKException as err:
        print(err)
    return ret


def get_local_ipv6_addresses():
    import subprocess

    # 使用subprocess.run来执行命令
    result = subprocess.run(['ipconfig'], capture_output=True, text=True)
    firstlist = result.stdout.split("\n")
    lines = []
    for index, item in enumerate(firstlist):
        if item and item != 'Windows IP 配置':
            lines.append(item)
    retdict = {}
    itemkey = ""
    # 获取到每行的记录
    for index, line in enumerate(lines):
        if line.startswith("   "):
            item = line.replace(" ", "").split(".:")
            key = item[0].replace(".", "")
            val = item[1] if len(item) > 1 else ""
            oldVal = retdict[itemkey][key] if key in retdict[itemkey] else ""
            if oldVal:
                retdict[itemkey][key].append(val)
            else:
                retdict[itemkey][key] = [val]
        else:
            itemkey = line.strip(":")
            retdict[itemkey] = {}
    return retdict


def getInet6ByName(ipconfigRet, name):
    ret = ""
    for item in ipconfigRet.get(name).get("IPv6地址"):
        if len(item.split(":")) == 8:
            ret = item
            break
    return ret


def main():
    # 1.检查当前的IPV6地址有没有变化
    # 2.如果没有变化，那么结束程序
    # 3.如果有变化，那么通过获取recordId
    # 4.如果没有获取到recordId，那么插入一笔
    # 5.如果获取到recordId，那么更新ipv6地址值
    client = getClient()
    hostname = platform.node()
    domain = os.environ.get("TENCENTCLOUD_DOMAIN")
    ipv6Address = getInet6ByName(get_local_ipv6_addresses(), "无线局域网适配器 WLAN")
    if not check(ipv6Address):
        return
    recordId = getRecordIdByHostName(client, hostname, domain)
    if not recordId:
        insertRecord(client, ipv6Address, hostname, domain)
    else:
        modifyRecordByRecordId(client, ipv6Address, recordId, hostname, domain)


if __name__ == '__main__':
    main()
