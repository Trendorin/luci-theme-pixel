# luci-theme-pixel: a monochrome pixel theme for OpenWrt LuCI
# Build with the OpenWrt SDK or buildroot: copy this directory to package/ and run
#   make package/luci-theme-pixel/compile
# Licensed under the Apache License 2.0.

include $(TOPDIR)/rules.mk

PKG_NAME:=luci-theme-pixel
PKG_VERSION:=1.0.2
PKG_RELEASE:=1

PKG_LICENSE:=Apache-2.0
PKG_LICENSE_FILES:=LICENSE
PKG_MAINTAINER:=Trendon <https://github.com/Trendorin>

include $(INCLUDE_DIR)/package.mk

define Package/luci-theme-pixel
  SECTION:=luci
  CATEGORY:=LuCI
  SUBMENU:=4. Themes
  TITLE:=Pixel: monochrome pixel theme with CRT touches
  URL:=https://github.com/Trendorin/luci-theme-pixel
  DEPENDS:=+luci-base
  PKGARCH:=all
endef

define Package/luci-theme-pixel/description
  A monochrome LuCI theme drawn on a pixel grid: a crisp 5x7 pixel font
  (Latin and Cyrillic), notched pixel frames, CRT scanlines, a hostname
  wordmark that decodes out of pixel noise, typed subtitles and stepped
  animations. Dark, light and automatic modes, phone layout, home-screen
  icons. Fonts and art are served by the router itself.
endef

define Build/Compile
endef

define Package/luci-theme-pixel/install
	$(INSTALL_DIR) $(1)/www
	$(CP) ./htdocs/* $(1)/www/
	$(INSTALL_DIR) $(1)/usr/share/ucode/luci
	$(CP) ./ucode/* $(1)/usr/share/ucode/luci/
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./root/etc/uci-defaults/30_luci-theme-pixel $(1)/etc/uci-defaults/
endef

define Package/luci-theme-pixel/postinst
#!/bin/sh
[ -n "$${IPKG_INSTROOT}" ] && exit 0
if [ -f /etc/uci-defaults/30_luci-theme-pixel ]; then
	( . /etc/uci-defaults/30_luci-theme-pixel ) && rm -f /etc/uci-defaults/30_luci-theme-pixel
fi
rm -rf /tmp/luci-indexcache* /tmp/luci-modulecache
exit 0
endef

define Package/luci-theme-pixel/prerm
#!/bin/sh
[ -n "$${IPKG_INSTROOT}" ] && exit 0
uci -q delete luci.themes.Pixel
if [ "$$(uci -q get luci.main.mediaurlbase)" = "/luci-static/pixel" ]; then
	uci set luci.main.mediaurlbase=/luci-static/bootstrap
fi
uci commit luci
rm -rf /tmp/luci-indexcache* /tmp/luci-modulecache
exit 0
endef

$(eval $(call BuildPackage,luci-theme-pixel))
