# encoding:utf-8
import sys
from jsonpath import jsonpath
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service  # 关键修复1：导入Service类

from common.douyu_request import dyreq
from common.logger import logger

Bags = 0
Own = 0

cookies = {}


def get_glow():
    """
    :return: 领取结果的基本格式
    """
    logger.info("------正在获取荧光棒------")
    go_room()
    glow_url = "/japi/prop/backpack/web/v1?rid=12306"
    glow_res = dyreq.request("get", glow_url)
    global Bags
    logger.info("------背包检查开始------")
    try:
        assert glow_res.status_code == 200
        assert glow_res.json()['msg'] == "success"
        if glow_res.json()['data']['list']:
            global Own
            try:
                Own = jsonpath(glow_res.json(), '$..list[?(@.id == 268)].count')[0]
                logger.info(f"当前拥有荧光棒{Own}个,给你喜欢的主播进行赠送吧")
            except TypeError as e:
                logger.error(f"背包当中没有荧光棒,但拥有其他礼物:{e}")
            Bags = 1
            logger.info("------背包检查结束------")
        else:
            logger.warning("当前背包中没有任何道具")
            logger.info("------背包检查结束------")
    except AssertionError:
        if glow_res.json()['msg'] == '请登录':
            logger.error("请更新COOKIE")
        else:
            logger.error("领取荧光棒时发生错误")
        logger.info("------背包检查结束------")
    return glow_res


def get_own():
    return Own


def glow_donate(num=1, room_id=12306):
    donate_url = "/japi/prop/donate/mainsite/v1"
    DATA = f"propId=268&propCount={num}&roomId={room_id}&bizExt={{\"yzxq\":{{}}}}"
    if Bags:
        donate_res = dyreq.request(method="post", path=donate_url, data=DATA)
        global Own
        try:
            assert donate_res.status_code == 200
            assert donate_res.json()['msg'] == "success"
            now_left = int(Own) - int(num)
            Own = now_left
            logger.info(f"向房间号{room_id}赠送荧光棒{num}个成功,当前剩余{now_left}个")
        except AssertionError:
            if donate_res.json()['msg'] == "用户没有足够的道具":
                logger.warning(f"向房间号{room_id}赠送荧光棒失败,当前背包中荧光棒数量为:{Own},而设定捐赠数量为{num}")
            else:
                logger.warning(donate_res.json()['msg'])


def go_room():
    # 关键修复2：使用Service类代替executable_path
    service = Service(executable_path=ChromeDriverManager().install())  # 自动管理驱动版本
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(service=service, options=chrome_options)  # 关键修复3：传递service参数

    logger.info("打开直播间")
    driver.get('https://www.douyu.com/8291425')
    dy_cookie = set_cookie(dyreq.cookie)
    for name, value in dy_cookie.items():
        driver.add_cookie({
            'domain': '.douyu.com',
            'name': name,
            'value': value,
            'path': '/',
            'httpOnly': False,
            'Secure': False
        })
    logger.info("刷新页面以完成登录")
    driver.refresh()
    WebDriverWait(driver, 30, 0.5).until(
        lambda d: d.find_element("xpath", "//div[contains(@class, 'UserInfo')]")
    )
    logger.info("成功以登陆状态进入页面")
    logger.info("再次刷新页面")
    driver.refresh()
    sleep(10)
    driver.quit()
    logger.info("关闭直播间")


def set_cookie(cookie):
    cookies = {}
    for line in cookie.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name] = value
    return cookies


if __name__ == '__main__':
    get_glow()
