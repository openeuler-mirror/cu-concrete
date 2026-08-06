Name:           cu-concrete
Version:        1.2
Release:        6
Summary:        A security hardening tool for system configuration

License:        MulanPSL v2
URL:            yuesl6@chinaunicom.cn
Source0:        %{name}.tar.gz
BuildArch:      noarch

# 工具依赖（构建时不需要编译，但需要一些脚本解释器）
BuildRequires:  python3, util-linux, bash
# 运行时依赖
Requires:       python3
Requires:       python3-devel
Requires:       python3-django-cors-headers
Requires:       python3-django-rest-framework
Requires:       python3-drf-yasg
Requires:       python3-pyyaml
Requires:       python3-whiptail-dialogs
Requires:       python3-pip
Requires:       openssh
Requires:       openssh-clients
Requires:       ansible
Requires:       python3-pandas
Requires:       uvicorn

%description
Cu-concrete is an automated system security hardening utility that enhances
operating system security by modifying system configurations such as user accounts,
services, network settings, file permissions, and audit policies.
It supports compliance with CIS, 等级保护, and other security standards.

%prep
%setup -q -n %{name}-%{version} -c
# %setup -q -n %{name}

%build
# 如果是纯脚本工具，无需编译，可留空或添加预处理脚本
# 例如：生成版本信息、检查依赖等
# echo "Building %{name}-%{version}"

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p %{buildroot}/opt/cu-concrete/
mkdir -p %{buildroot}/usr/bin/
mkdir -p %{buildroot}/usr/share/doc/cu-concrete/
mkdir -p %{buildroot}/var/log/cu-concrete/
mkdir -p %{buildroot}/etc/cu-concrete/
mkdir -p %{buildroot}/usr/share/applications/
mkdir -p %{buildroot}/usr/share/cu-concrete/

# 复制主程序与配置文件
cp -a * %{buildroot}/opt/cu-concrete/
rm -f %{buildroot}/opt/cu-concrete/*.spec
rm -f %{buildroot}/opt/cu-concrete/*.md

# 复制 .desktop 和图标文件
cp -a cu-concrete.desktop %{buildroot}/usr/share/applications/
cp -a cu-concrete-logo.svg %{buildroot}/usr/share/cu-concrete/

# 创建启动脚本软链接
ln -sf /opt/cu-concrete/main.py %{buildroot}/usr/bin/cu-concrete

# 复制文档
cp -a README.md LICENSE %{buildroot}/usr/share/doc/cu-concrete/

%files
%defattr(-,root,root)
/opt/cu-concrete/
/usr/bin/cu-concrete
/usr/share/doc/cu-concrete/*
/etc/cu-concrete/
/var/log/cu-concrete/

/usr/share/applications/%{name}.desktop
/usr/share/cu-concrete/%{name}-logo.svg

%post
# 安装后操作：设置权限、注册服务（可选）
chmod +x /opt/cu-concrete/*.py
chmod +x /opt/cu-concrete/*.sh
sed -i 's/\r$//' /opt/cu-concrete/*.py /opt/cu-concrete/*.sh
chmod 755 /opt/cu-concrete
find /opt/cu-concrete -type d -exec chmod 755 {} \;
chown -R root:root /opt/cu-concrete/

# 更新桌面数据库 - 让系统能识别新的.desktop文件
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications/ || true
fi

echo "cu-concrete installed successfully."

%postun
# 卸载后清理
rm -rf /opt/cu-concrete/
rm -rf /var/log/cu-concrete/
rm -rf /etc/cu-concrete/

%changelog
* Fri Jul 17 2026 YueShuolei <yuesl6@chinaunicom.cn> - 1.2-6
- fix: modify desktop name

* Thu Jul 16 2026 YueShuolei <yuesl6@chinaunicom.cn> - 1.2-5
- fix: Bug fixes for security hardening items

* Tue Jun 16 2026 YueShuolei <yuesl6@chinaunicom.cn> - 1.2-4
- feat: Fix uvicorn package and desktop display bug

* Fri May 08 2026 YueShuolei <yuesl6@chinaunicom.cn> - 1.2-3
- feat: Add Patent Module for Task Processing

* Fri Feb 27 2026 GuoCe <guoc63@chinaunicom.cn> - 1.2-2
- feat: use shred to enhance rm command secure erasure

* Wed Sep 10 2025 Kun Liu <liuk311@chinaunicom.cn> - 1.2-1
- Initial release of cu-concrete