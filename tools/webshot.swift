// Offline page renderer: loads a local HTML file in an off-screen WKWebView
// (scripts run), optionally runs JavaScript, and saves a PNG snapshot.
// Usage: webshot FILE WIDTH HEIGHT OUT.png [--full] [--js CODE] [--wait SECONDS] [--dark]
import AppKit
import WebKit

let args = CommandLine.arguments
guard args.count >= 5 else { print("usage: webshot FILE WIDTH HEIGHT OUT.png [--full] [--js CODE] [--wait S] [--dark]"); exit(2) }
let file = URL(fileURLWithPath: args[1])
let width = CGFloat(Double(args[2])!)
var height = CGFloat(Double(args[3])!)
let out = URL(fileURLWithPath: args[4])
var full = false, js: String? = nil, wait = 1.2, dark = false, still = false
var i = 5
while i < args.count {
  switch args[i] {
  case "--full": full = true
  case "--js": i += 1; js = args[i]
  case "--wait": i += 1; wait = Double(args[i])!
  case "--dark": dark = true
  case "--still": still = true
  default: break
  }
  i += 1
}

final class Shot: NSObject, WKNavigationDelegate {
  let web: WKWebView
  let window: NSWindow
  init(width: CGFloat, height: CGFloat) {
    let cfg = WKWebViewConfiguration()
    cfg.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
    // Theme and motion are set before the page's own scripts run, like a returning visitor.
    var boot = "try{localStorage.setItem('theme','" + (dark ? "dark" : "light") + "')}catch(e){};"
    if still {
      boot += "document.addEventListener('DOMContentLoaded',function(){var s=document.createElement('style');s.textContent='*,*::before,*::after{transition:none!important;animation:none!important}';document.head.appendChild(s)});"
    }
    cfg.userContentController.addUserScript(WKUserScript(source: boot, injectionTime: .atDocumentStart, forMainFrameOnly: true))
    web = WKWebView(frame: NSRect(x: 0, y: 0, width: width, height: height), configuration: cfg)
    window = NSWindow(contentRect: web.frame, styleMask: [.borderless], backing: .buffered, defer: false)
    window.contentView = web
    super.init()
    web.navigationDelegate = self
  }
  func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { self.prepare() }
  }
  func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) { print("fail", error); exit(1) }
  func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) { print("fail", error); exit(1) }
  func prepare() {
    web.evaluateJavaScript((js ?? "") + ";1") { _, err in
      if let err = err { print("js error:", err) }
      DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { self.measure() }
    }
  }
  func measure() {
    guard full else { DispatchQueue.main.asyncAfter(deadline: .now() + wait) { self.snap() }; return }
    web.evaluateJavaScript("Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)") { v, _ in
      let h = CGFloat((v as? NSNumber)?.doubleValue ?? Double(height))
      self.web.frame = NSRect(x: 0, y: 0, width: width, height: h)
      self.window.setContentSize(NSSize(width: width, height: h))
      // A full-page shot has no scrolling, so show what would arrive on scroll.
      self.web.evaluateJavaScript("document.querySelectorAll('.pending').forEach(e=>e.classList.remove('pending'));1") { _, _ in
        DispatchQueue.main.asyncAfter(deadline: .now() + wait) { self.snap() }
      }
    }
  }
  func snap() {
    let c = WKSnapshotConfiguration()
    c.rect = web.bounds
    c.snapshotWidth = NSNumber(value: Double(width))
    web.takeSnapshot(with: c) { img, err in
      guard let img = img, let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
            let png = rep.representation(using: .png, properties: [:]) else { print("snapshot failed", err as Any); exit(1) }
      try! png.write(to: out)
      print("saved", out.path, Int(self.web.bounds.width), "x", Int(self.web.bounds.height))
      exit(0)
    }
  }
}

let app = NSApplication.shared
app.setActivationPolicy(.prohibited)
let shot = Shot(width: width, height: height)
shot.web.loadFileURL(file, allowingReadAccessTo: URL(fileURLWithPath: "/"))
DispatchQueue.main.asyncAfter(deadline: .now() + 30) { print("timeout"); exit(1) }
app.run()
