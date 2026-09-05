import QtQuick
import Quickshell.Io
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "omarchy.power"
  ipcTarget: "omarchy.power"
  property var reading: ({})
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight
  function refresh() { if (!probe.running) probe.running = true }
  onOpenedChanged: if (opened) refresh()

  WidgetButton {
    id: button
    bar: root.bar
    text: "Battery"
    onPressed: root.toggle()
  }
  Process {
    id: probe
    command: ["bash", "-lc", "~/.local/bin/uconsole-battery"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: { try { root.reading = JSON.parse(text) } catch (e) { root.reading = {error:"Battery reading unavailable"} } }
    }
  }
  Timer { interval: 5000; repeat: true; running: root.opened; onTriggered: root.refresh() }
  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keys
    contentWidth: panel.fittedContentWidth(420)
    contentHeight: panel.fittedContentHeight(content.implicitHeight)
    PanelKeyCatcher {
      id: keys
      anchors.fill: parent
      onCloseRequested: root.close()
      onActivateRequested: root.refresh()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      Column {
        id: content
        width: parent.width
        spacing: 15
        Repeater {
          model: [
            "Battery",
            root.reading.error || (root.reading.status || "Reading…"),
            root.reading.voltage === undefined ? "" : Number(root.reading.voltage).toFixed(2) + " V   ·   " + Math.abs(root.reading.current).toFixed(2) + " A",
            root.reading.power === undefined ? "" : Number(root.reading.power).toFixed(1) + " W battery power",
            root.reading.percent === undefined ? "" : "Charge gauge: " + root.reading.percent + "%" + (root.reading.suspect ? " — unreliable" : " — estimate"),
            root.reading.suspect ? "The charge gauge needs calibration. Voltage and current are live measurements." : "Voltage and current are live measurements. Charge percentage depends on calibration.",
            "Enter refresh · Esc close"
          ]
          delegate: Text {
            required property string modelData
            required property int index
            width: content.width
            text: modelData
            textFormat: Text.PlainText
            wrapMode: Text.WordWrap
            color: index === 4 && root.reading.suspect ? "#FFD166" : Color.foreground
            font.family: root.bar ? root.bar.fontFamily : "sans-serif"
            font.pixelSize: index === 0 ? 24 : index === 6 ? 17 : 20
            font.bold: index === 0 || index === 2
          }
        }
      }
    }
  }
}
