# Maintainer: Hannele Ruiz <justlemoncl@gmail.com>
pkgname=rptconv
pkgver=r33.4bbfe31
pkgrel=1
pkgdesc="Script to convert repeaters from the Chilean list of repeaters provided by SUBTEL into CHIRP compatible lists"
url="https://github.com/justalemon/RPTConv"
arch=("any")
license=("MIT")
depends=()
if [[ -v MAKEDEB_VERSION ]]; then
    depends+=(python3 python3-typer python3-requests python3-openpyxl python3-colorama)
else
    depends+=(python python-typer python-requests python-openpyxl python-colorama)
fi
makedepends=()
provides=("${pkgname%-git}")
source=("src-$pkgname::git+${url}.git")
sha256sums=('SKIP')

pkgver() {
    cd "src-$pkgname"
    local format
    if [[ -v MAKEDEB_VERSION ]]; then
        format="%s.%s"
    else
        format="r%s.%s"
    fi
    printf "$format" "$(git rev-list --count HEAD)" "$(git rev-parse --short=7 HEAD)"
}

package() {
    cd "src-$pkgname"
    install -m 775 -DT "$pkgname.py" "$pkgdir/usr/bin/$pkgname"
}
