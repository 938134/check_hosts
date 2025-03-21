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
3.167.192.127               tmdb.org
3.167.192.35                api.tmdb.org
3.167.192.77                files.tmdb.org
3.167.212.118               themoviedb.org
3.167.212.53                api.themoviedb.org
3.167.212.33                www.themoviedb.org
18.154.132.71               auth.themoviedb.org
143.244.50.83               image.tmdb.org
143.244.50.83               images.tmdb.org
52.94.228.167               imdb.com
18.164.172.55               www.imdb.com
52.94.228.167               secure.imdb.com
18.164.172.55               s.media-imdb.com
52.94.237.74                us.dd.imdb.com
18.164.172.55               www.imdb.to
44.215.137.99               origin-www.imdb.com
199.232.45.16               ia.media-imdb.com
18.154.130.110              thetvdb.com
3.167.194.87                api.thetvdb.com
199.232.45.16               ia.media-imdb.com
199.232.45.16               f.media-amazon.com
3.167.212.54                imdb-video.media-imdb.com
140.82.114.25               alive.github.com
20.205.243.168              api.github.com
185.199.110.133             avatars.githubusercontent.com
185.199.111.133             avatars0.githubusercontent.com
185.199.111.133             avatars1.githubusercontent.com
185.199.109.133             avatars2.githubusercontent.com
185.199.109.133             avatars3.githubusercontent.com
185.199.108.133             avatars4.githubusercontent.com
185.199.111.133             avatars5.githubusercontent.com
185.199.108.133             camo.githubusercontent.com
140.82.112.22               central.github.com
185.199.108.133             cloud.githubusercontent.com
20.205.243.165              codeload.github.com
140.82.112.22               collector.github.com
185.199.111.133             desktop.githubusercontent.com
185.199.108.133             favicons.githubusercontent.com
20.205.243.166              gist.github.com
3.5.30.214                  github-cloud.s3.amazonaws.com
52.216.52.241               github-com.s3.amazonaws.com
3.5.8.151                   github-production-release-asset-2e65be.s3.amazonaws.com
3.5.8.151                   github-production-repository-file-5c1aeb.s3.amazonaws.com
52.216.56.225               github-production-user-asset-6210df.s3.amazonaws.com
192.0.66.2                  github.blog
20.205.243.166              github.com
140.82.114.18               github.community
185.199.111.154             github.githubassets.com
151.101.77.194              github.global.ssl.fastly.net
185.199.109.153             github.io
185.199.108.133             github.map.fastly.net
185.199.110.153             githubstatus.com
140.82.114.25               live.github.com
185.199.108.133             media.githubusercontent.com
185.199.109.133             objects.githubusercontent.com
13.107.42.16                pipelines.actions.githubusercontent.com
185.199.111.133             raw.githubusercontent.com
185.199.110.133             user-images.githubusercontent.com
13.107.246.73               vscode.dev
140.82.112.22               education.github.com
185.199.111.133             private-user-images.githubusercontent.com
```

该内容会自动定时更新， 数据更新时间：2025-03-21T20:47:56+08:00

#### 2.1.2 IPv6地址复制下面的内容

```bash
2600:9000:27e0:4a00:10:db24:6940:93a1              tmdb.org
2600:9000:27e0:800:10:fb02:4000:93a1               api.tmdb.org
2600:9000:27e0:4000:5:da10:7440:93a1               files.tmdb.org
2600:9000:27e3:3a00:e:5373:440:93a1                themoviedb.org
2600:9000:27e3:8600:c:174a:c400:93a1               api.themoviedb.org
2600:9000:27e3:ee00:e:5373:440:93a1                www.themoviedb.org
2600:9000:24db:8000:16:e4a1:eb00:93a1              auth.themoviedb.org
2400:52e0:1a01::907:1                              image.tmdb.org
2400:52e0:1a01::907:1                              images.tmdb.org
2a04:4e42:48::272                                  ia.media-imdb.com
2a04:4e42:48::272                                  ia.media-imdb.com
2a04:4e42:48::272                                  f.media-amazon.com
2606:50c0:8002::154                                avatars.githubusercontent.com
2606:50c0:8003::154                                media.githubusercontent.com
2620:1ec:21::16                                    pipelines.actions.githubusercontent.com
2606:50c0:8002::154                                raw.githubusercontent.com
2606:50c0:8000::154                                user-images.githubusercontent.com
```

该内容会自动定时更新， 数据更新时间：2025-03-21T20:47:56+08:00

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
