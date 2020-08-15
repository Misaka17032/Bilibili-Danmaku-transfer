# Bilibili-Danmaku-transfer
通过python实现把视频当中的弹幕迁移至另外一个视频。

## 运行环境要求
```
python3
```

## 使用方法
一、下载本项目当中的`shoot.py`。

二、登录你的[B站账号](https://passport.bilibili.com/login)，如果你已登陆则可跳过这一步。

三、获取`sessdata`和`csrf`值。

`sessdata`是Cookies中`SESSDATA`键对应的值，`csrf`是Cookies中`bili_jct`键对应的值。具体获取cookies值的方法可以自行百度，这里以Chrome浏览器为例。

点开B站，可以看见在浏览器左上角有一个锁的标志，点开后里面有一个Cookies的选项。

![](https://res.passkou.com/image/20200812000443.png)

点击这个选项，在当中的文件夹当中找到`SESSDATA`键和`bili_jct`键。记下它们的值。

![](https://res.passkou.com/image/20200812000554.png)

**千万不要泄露这两个值，否则你的账号将可能会遭受盗号的风险！**

四、运行`shoot.py`，并且按照提示依次输入值。

五、等待程序运行。由于B站有弹幕发送频率超过15秒一次就会打断的机制，搬运大量弹幕时会花费比较长的时间。

注意在程序运行时电脑不能处于断网、休眠、关机等状态，否则脚本会停止运行。

推荐使用服务器运行。

## 致谢

感谢由[bilibili_api](https://github.com/Passkou/bilibili_api)提供的技术支持。
