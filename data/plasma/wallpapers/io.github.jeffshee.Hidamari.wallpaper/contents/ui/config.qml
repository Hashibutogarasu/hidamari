import QtQuick 2.0
import QtQuick.Controls 2.0 as QQC2
import Qt.labs.platform 1.1 as Labs
import org.kde.kirigami 2.5 as Kirigami
import org.kde.plasma.core 2.0 as PlasmaCore

Kirigami.FormLayout {
    id: root
    twinFormLayouts: parentLayout

    property alias cfg_Volume: volumeSlider.value
    property alias cfg_Mute: muteCheckBox.checked
    property alias formLayout: root

    property bool suppressWrite: true

    function shellQuote(s) {
        return "'" + s.replace(/'/g, "'\\''") + "'"
    }

    function urlToPath(url) {
        var path = url.toString()
        if (path.indexOf("file://") === 0)
            path = path.substring(7)
        return decodeURIComponent(path)
    }

    PlasmaCore.DataSource {
        id: bridge
        engine: "executable"
        connectedSources: []
        onNewData: {
            var exitCode = data["exit code"]
            var stdout = (data["stdout"] || "").trim()
            disconnectSource(sourceName)
            if (exitCode !== 0)
                return
            if (sourceName.indexOf("get is_paused_by_user") !== -1) {
                var wasPaused = (stdout === "True")
                bridge.connectSource("hidamari --dbus set is_paused_by_user " + (!wasPaused))
                bridge.connectSource(
                    "hidamari --dbus call " + (wasPaused ? "start_playback" : "pause_playback")
                )
                return
            }
            suppressWrite = true
            if (sourceName.indexOf("get volume") !== -1)
                volumeSlider.value = parseInt(stdout)
            else if (sourceName.indexOf("get is_mute") !== -1)
                muteCheckBox.checked = (stdout === "True")
            suppressWrite = false
        }
    }

    Component.onCompleted: {
        bridge.connectSource("hidamari --dbus get volume")
        bridge.connectSource("hidamari --dbus get is_mute")
    }

    QQC2.Slider {
        id: volumeSlider
        Kirigami.FormData.label: "Volume:"
        from: 0
        to: 100
        stepSize: 1
        onValueChanged: {
            if (!suppressWrite)
                bridge.connectSource("hidamari --dbus set volume " + Math.round(value))
        }
    }

    QQC2.CheckBox {
        id: muteCheckBox
        Kirigami.FormData.label: "Mute:"
        text: "Mute audio"
        onCheckedChanged: {
            if (!suppressWrite)
                bridge.connectSource("hidamari --dbus set is_mute " + checked)
        }
    }

    Labs.FileDialog {
        id: videoFileDialog
        title: "Select a video file"
        onAccepted: {
            bridge.connectSource(
                "hidamari --dbus call video "
                + shellQuote(urlToPath(file)) + " " + shellQuote("Default")
            )
        }
    }

    QQC2.Button {
        Kirigami.FormData.label: "Source:"
        text: "Choose video file…"
        onClicked: videoFileDialog.open()
    }

    QQC2.Button {
        text: "Play/Pause"
        onClicked: bridge.connectSource("hidamari --dbus get is_paused_by_user")
    }
}
