import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// User-owned text module. BarWidget supplies writable host-injected properties.
BarWidget {
  id: root
  property string outputText: ""
  property string outputTooltip: ""
  property bool outputActive: false
  readonly property bool opened: nativePanel.item ? nativePanel.item.opened : false
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight
  function open() { if (nativePanel.item) nativePanel.item.open() }
  function close() { if (nativePanel.item) nativePanel.item.close() }
  function toggle() { if (nativePanel.item) nativePanel.item.toggle() }
  function configurePanel() {
    if (!nativePanel.item) return
    nativePanel.item.bar = root.bar
    nativePanel.item.moduleName = root.moduleName
    // Keep the native popup and its anchor, replacing only its icon with text.
    for (var child of nativePanel.item.children) {
      if ("triggerPress" in child && "text" in child) {
        child.opacity = 0
        child.interactive = false
      }
    }
  }
  onBarChanged: configurePanel()
  Loader {
    id: nativePanel
    anchors.fill: parent
    source: {
      var path = String(root.setting("panelSource", ""))
      return path.startsWith("~/") ? Util.fileUrl(Quickshell.env("HOME") + path.slice(1)) : path
    }
    onLoaded: root.configurePanel()
  }

  function update(raw) {
    var data = Util.parseModuleJson(raw)
    var klass = data.class || data.alt || ""
    outputText = data.text || String(raw || "").trim()
    outputTooltip = data.tooltip || String(setting("tooltip", ""))
    outputActive = klass === "active" || (Array.isArray(klass) && klass.indexOf("active") !== -1)
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.outputText || String(root.setting("text", ""))
    tooltipText: root.outputTooltip || String(root.setting("tooltip", ""))
    active: root.outputActive
    fontSize: Number(root.setting("fontSize", 20))
    horizontalMargin: 7.5
    verticalPadding: 6
    onPressed: function(mouseButton) {
      if (nativePanel.item) { root.toggle(); return }
      var key = mouseButton === Qt.RightButton ? "onRightClick" : mouseButton === Qt.MiddleButton ? "onMiddleClick" : "onClick"
      var command = String(root.setting(key, ""))
      if (command && root.bar) root.bar.run(command)
    }
  }

  Process {
    id: statusProcess
    command: ["bash", "-lc", String(root.setting("exec", ""))]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.update(text)
    }
  }
  Timer {
    interval: Math.max(1, Number(root.setting("interval", 5))) * 1000
    running: String(root.setting("exec", "")) !== ""
    repeat: true
    triggeredOnStart: true
    onTriggered: if (!statusProcess.running) statusProcess.running = true
  }
}
