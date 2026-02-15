# Maintainer: Nirakar Jena <jenanirakar60@gmail.com>
pkgname=loglens
pkgver=1.0.0
pkgrel=1
pkgdesc="Linux log viewer with interactive Terminal UI and powerful filtering engine"
arch=('any')
url="https://github.com/nirakar24/loglens"
license=('MIT')
depends=('python' 'python-textual')
makedepends=('python-setuptools')
optdepends=('systemd: for journalctl log source support')
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py build
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py install --root="$pkgdir" --optimize=1 --skip-build

    # Install the TUI launcher
    install -Dm755 logtui.py "$pkgdir/usr/bin/logtui"
    
    # Install license
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    
    # Install documentation
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}
