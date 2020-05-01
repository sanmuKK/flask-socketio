## flask+gunicorn+nginx

API地址：www.showdoc.cc/ljlsanmu

聊天室地址：47.107.243.207

## 服务器

 ####  安装centos7系统

1. 1.  系统选择CentOS系统就好（推荐选择CentOS7系统）
   2.  用户名：root
   3.  密码自己设定（自己记住）

    4.  通过ssh工具登录服务器
        1. 这里推荐大家使用Putty进行登录。（可以自己百度下载一个，putty开源） 注意要开放ssh连接的端口，一般默认是22，（重装系统是默认开启的）为了网站安全推荐大家更换ssh登录端口。设置为不常用的端口。
2. putty登录服务器方法。只需要设置好IP地址，端口号，选择SSH。再点击open即可连接服务器（第一次连接会出来一个安全信息，后面就不会再有，点确定就好了）
3. 输入账号密码（账号就是root，密码是安装系统的时候）登录。（lunix下输入密码是没有光标提示操作的，直接输入完了直接回车）

   3. 安装宝塔面板。
      1. 执行以下代码进行安装宝塔6.9免费版。

```
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh
```

​			复制对应的命令在putty中执行，然后再输入y即可。（等待安装完成）

4. 注意！安装成功的时候账号密码一定要保存下来。（可以复制写在记事本）
   制账号上面的：http：//xxx.xxx.xxx.xxx:8888/(这个就是你的IP地址：8888端口)
   在浏览器的网址输入，登录到宝塔面板的后台。

​	5.刷新浏览器页面即可。

​	6.在网站选项添加一个新站并加上自己的域名及端口号

#### python3安装

```                        cd .. 到   root
which python
mkdir /usr/local/python3 
cd /usr/local/python3                   
安装依赖
yum -y groupinstall "Development tools"
yum -y install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel

安装python3（3.6.2）
wget https://www.python.org/ftp/python/3.6.2/Python-3.6.2.tar.xz

蓝奏云下载:https://www.lanzous.com/i7x8kxg 密码:3bhk（下载好后传入刚创建的python3文件夹）

tar -xvJf  Python-3.6.2.tar.xz
cd Python-3.6.2
./configure --prefix=/usr/local/python3
make && make install

创建软链接
ln -s /usr/local/python3/bin/python3 /usr/bin/python3
ln -s /usr/local/python3/bin/pip3 /usr/bin/pip3
```

#### 搭建web环境

* 创建虚拟环境
* 安装flask
* 安装和配置gunicorn
* 配置nginx

```
pip3 install --upgrade virtualenv
mkdir test
cd test             (这个test在是/usr/local/python3/Python-3.6.2的/www/wwwroot/里)
virtualenv -p python3 .env

进入虚拟环境安装flask以及需要的模块（包括eventlet）
source .env/bin/activate
离开虚拟环境
deactivate  
```

* 在test文件夹把代码放入test.py
* 安装gunicorn

1. 安装gunicorn（进入虚拟环境安装source .env/bin/activate）

```
pip3 install gunicorn
```

2.启动gunicorn（进入虚拟环境启动source .env/bin/activate）

```
gunicorn -b 127.0.0.1:8787 -k eventlet -w 1 -D test:app
pstree -ap|grep gunicorn（获取gunicorn进程树，在www.test.com文件夹下的虚拟文件夹使用，其中主进程也就是第一个就是下面要kill的）
kill -HUP ****（重启gunicorn，在www.test.com文件夹下的虚拟文件夹使用，****是gunicorn主进程,通过获取进程树查看）
kill -15 ****(kill进程)
```




* 配置nginx(加入宝塔对应域名的配置文件中并注释 include enable-php-56.conf;)

```
    location / {
        root /www/wwwroot/www.test.com/static/dist/;
        index  index.html index.htm;
    }
    location /api {
        proxy_pass http://127.0.0.1:8787;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For 		$proxy_add_x_forwarded_for;
    }
    location /socket.io {
        proxy_pass http://127.0.0.1:8787/socket.io;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
    location /static {
        alias /www/wwwroot/www.test.com/static;
    }
```

