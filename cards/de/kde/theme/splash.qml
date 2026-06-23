/*
    SPDX-FileCopyrightText: 2014 Marco Martin <mart@kde.org>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    color: "black"

    property int stage

    onStageChanged: {
        if (stage == 2) {
            introAnimation.running = true;
        } else if (stage == 5) {
            introAnimation.target = busyIndicator;
            introAnimation.from = 1;
            introAnimation.to = 0;
            introAnimation.running = true;
        }
    }

    Item {
        id: content
        anchors.fill: parent
        opacity: 0

        Image {
            id: logo
            // Match SDDM/lockscreen avatar positioning.
            readonly property real size: Kirigami.Units.gridUnit * 8

            anchors.centerIn: parent

            asynchronous: true
            source: "images/anatase.svg"

            sourceSize.width: size
            sourceSize.height: size
        }

        Item {
            id: busyIndicator
            readonly property real size: Kirigami.Units.gridUnit * 1.3

            width: size
            height: size
            y: logo.y + logo.height + (parent.height - logo.y - logo.height) / 2 - height / 2
            anchors.horizontalCenter: parent.horizontalCenter

            Canvas {
                id: spinnerRing
                anchors.fill: parent

                onPaint: {
                    const ctx = getContext("2d");
                    const lineWidth = Math.max(2, width * 0.16);
                    const radius = (Math.min(width, height) - lineWidth) / 2;
                    const centerX = width / 2;
                    const centerY = height / 2;

                    ctx.clearRect(0, 0, width, height);
                    ctx.lineCap = "round";
                    ctx.lineWidth = lineWidth;

                    ctx.beginPath();
                    ctx.strokeStyle = "rgba(239, 240, 241, 0.16)";
                    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
                    ctx.stroke();

                    ctx.beginPath();
                    ctx.strokeStyle = "#eff0f1";
                    ctx.arc(centerX, centerY, radius, Math.PI * 1.05, Math.PI * 1.65);
                    ctx.stroke();
                }
            }

            RotationAnimator on rotation {
                from: 0
                to: 360
                // Keep the splash spinner independent from user animation scale.
                duration: 1000
                loops: Animation.Infinite
                running: Kirigami.Units.longDuration > 1
            }
        }
    }

    OpacityAnimator {
        id: introAnimation
        running: false
        target: content
        from: 0
        to: 1
        duration: Kirigami.Units.veryLongDuration * 2
        easing.type: Easing.InOutQuad
    }
}
