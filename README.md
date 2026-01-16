# CheckTMDB

每日自动更新TMDB，themoviedb、thetvdb 国内可正常连接IP，解决DNS污染，供tinyMediaManager(TMM削刮器)、Kodi的刮削器、群晖VideoStation的海报墙、Plex Server的元数据代理、Emby Server元数据下载器、Infuse、Nplayer等正常削刮影片信息。

## 一、前景

自从我早两年使用了黑群NAS以后，下了好多的电影电视剧，发现电视端无法生成正常的海报墙。查找资料得知应该是 themoviedb.org、tmdb.org 无法正常访问，因为DNS受到了污染无法正确解析到TMDB的IP，故依葫芦画瓢写了一个python脚本，每日定时通过[dnschecker](https://dnschecker.org/)查询出最佳IP，并自动同步到路由器外挂hosts，可正常削刮。

**本项目无需安装任何程序**

通过修改本地、路由器 hosts 文件，即可正常削刮影片信息。

## 二、使用方法

### 2.1 手动方式

#### 2.1.1 IPv4地址复制下面的内容

```bash
3.169.231.97                api.themoviedb.org
3.167.192.35                api.tmdb.org
13.225.117.96               www.themoviedb.org
3.170.218.86                api.thetvdb.com
148.113.196.166             webservice.fanart.tv
149.154.166.110             api.telegram.org
43.135.106.227              qyapi.weixin.qq.com
35.73.126.78                slack.com
151.101.192.223             pypi.org
20.200.245.247              github.com
20.200.245.246              codeload.github.com
20.200.245.245              api.github.com
185.199.111.133             raw.githubusercontent.com
18.164.154.32               image.tmdb.org
109.61.83.251               images.tmdb.org
```

该内容会自动定时更新， 数据更新时间：2026-01-16T15:25:18+08:00

#### 2.1.2 IPv6地址复制下面的内容

```bash
2600:9000:2864:ce00:c:174a:c400:93a1               api.themoviedb.org
2600:9000:27e0:ee00:10:fb02:4000:93a1              api.tmdb.org
2600:9000:21d3:b400:e:5373:440:93a1                www.themoviedb.org
2001:67c:4e8:f004::9                               api.telegram.org
2a04:4e42:400::223                                 pypi.org
2606:50c0:8003::154                                raw.githubusercontent.com
2400:52e0:1501::1189:1                             image.tmdb.org
2400:52e0:1501::1143:1                             images.tmdb.org
```

该内容会自动定时更新， 数据更新时间：2026-01-16T15:25:18+08:00

> [!NOTE]
> 由于项目搭建在Github Aciton，延时数据获取于Github Action 虚拟主机网络环境，请自行测试可用性，建议使用本地网络环境自动设置。

#### 2.1.3 修改 hosts 文件

hosts 文件在每个系统的位置不一，详情如下：

- Windows 系统：`C:\Windows\System32\drivers\etc\hosts`
- Linux 系统：`/etc/hosts`
- Mac（苹果电脑）系统：`/etc/hosts`
- Android（安卓）系统：`/system/etc/hosts`
- iPhone（iOS）系统：`/etc/hosts`

修改方法，把第一步的内容复制到文本末尾：

1. Windows 使用记事本。
2. Linux、Mac 使用 Root 权限：`sudo vi /etc/hosts`。
3. iPhone、iPad 须越狱、Android 必须要 root。

#### 2.1.4 激活生效

大部分情况下是直接生效，如未生效可尝试下面的办法，刷新 DNS：

1. Windows：在 CMD 窗口输入：`ipconfig /flushdns`

2. Linux 命令：`sudo nscd restart`，如报错则须安装：`sudo apt install nscd` 或 `sudo /etc/init.d/nscd restart`

3. Mac 命令：`sudo killall -HUP mDNSResponder`

**Tips：** 上述方法无效可以尝试重启机器。

### 2.2 自动方式

#### 2.2.1 安装 SwitchHosts

GitHub 发行版：https://github.com/oldj/SwitchHosts/releases/latest

#### 2.2.2 添加 hosts

点击左上角“+”，并进行以下配置：

- Hosts 类型：`远程`
- Hosts 标题：任意
- URL  `https://raw.githubusercontent.com/938134/check_hosts/refs/heads/main/hosts`
- 自动刷新：`1 小时`

#### 2.2.3 启用 hosts

在左侧边栏启用 hosts，首次使用时软件会自动获取内容。如果无法连接到 GitHub，可以尝试用同样的方法添加 [GitHub520](https://github.com/521xueweihan/GitHub520) hosts。

## 其他

- [x] 自学薄弱编程基础，大部分代码基于AI辅助生成，此项目过程中，主要人为解决的是：通过 [dnschecker](https://dnschecker.org/) 提交时，通过计算出正确的udp参数，获取正确的csrftoken，携带正确的referer提交！
- [x] README.md 及 部分代码 参考[GitHub520](https://github.com/521xueweihan/GitHub520)
- [x] * 本项目仅在本机测试通过，如有问题欢迎提 [issues](https://github.com/cnwikee/CheckTMDB/issues/new)
