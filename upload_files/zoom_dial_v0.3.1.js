/*
Marco Name: zoom_dial_v0.3.1

Source Original Source-Code: for WebEx: https://github.com/CiscoDevNet/roomdevices-macros-samples/tree/master/Join%20Webex%20with%20Prompt%20for%20Pin%20before%20connect
Info on how a dialing link has to be formatted: https://support.zoom.us/hc/en-us/articles/201854563-Start-a-Meeting-from-an-H-323-SIP-Endpoint

Modifications by stuerzenhofecker.sandro@bcg.com

ZoomDial V0.3.1
*/
const xapi = require('xapi');

const KEYBOARD_TYPES = {
    NUMERIC: 'Numeric',
    SINGLELINE: 'SingleLine',
    PASSWORD: 'Password',
    PIN: 'PIN'
};


const INROOMCONTROL_ZOOMCONTROL_PANELID = 'zoom_meeting';

//only digits and only a certain amount are allowed with those
const REGEXP_NUMERIC_1TO15 = /^([0-9]{1,15})$/;
const REGEXP_NUMERIC_0TO10 = /^([0-9]{0,10})$/;
const REGEXP_NUMERIC_6 = /^([0-9]{6})$/;
const REGEXP_ALPHANUMERIC_1TO15 = /^([@*_\-\w]{1,15})$/;


const GLOBAL_DIALPOSTFIX_URL = '@zoomcrc.com';
const DEFAULT_DIALPREFIX = 'meet';

const DIALPAD_MEETINGID_ID = 'meetingId_pad';
const DIALPAD_MEETINGPINORPASSWORD_ID = 'meetingpinorpassword_pad';
const DIALPAD_HOSTKEY_ID = 'hostkey_pad';

let meetingID = '';
let meetingPinOrPassword = '';
let hostKey = '';

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showMeetingNrDialPad(text) {
    xapi.command("UserInterface Message TextInput Display", {
        InputType: KEYBOARD_TYPES.NUMERIC,
        Placeholder: 'meeting ID e.g. 123456789',
        Title: "Join Zoom Meeting",
        Text: text,
        SubmitText: "Next",
        FeedbackId: DIALPAD_MEETINGID_ID
    }).catch((error) => {
        console.error(error);
    });
}

function showMeetingPinOrPasswordDialPad(text) {
    xapi.command("UserInterface Message TextInput Display", {
        InputType: KEYBOARD_TYPES.NUMERIC,
        Placeholder: "Meeting Pin/Password",
        Title: "Enter the meeting Pin or Password",
        Text: text,
        SubmitText: "Next",
        FeedbackId: DIALPAD_MEETINGPINORPASSWORD_ID
    }).catch((error) => {
        console.error(error);
    });
}

function showHostKeyDialPad(text) {
    xapi.command("UserInterface Message TextInput Display", {
        InputType: KEYBOARD_TYPES.NUMERIC,
        Placeholder: "Host Key (optional)",
        Title: "Enter the Host Key or leave blank",
        Text: text,
        SubmitText: "Dial",
        FeedbackId: DIALPAD_HOSTKEY_ID
    }).catch((error) => {
        console.error(error);
    });
}

function getMeetingIdFormatted(id) {
    //avoid any errors caused by a too short ID
    if (id.length > 6) {
        return id.substring(0, 3) + '-' + id.substring(3, 6) + '-' + id.substring(6, id.length);
    }else{
        console.log("Meeting ID " + id + "could not be formatted correctly");
        return id;
    }
}

/* This is the listener for the in-room control panel button that will trigger the dial panel to appear */
xapi.event.on('UserInterface Extensions Panel Clicked', (event) => {
    //is the Zoom Button on the home screen pushed?
    if (event.PanelId === INROOMCONTROL_ZOOMCONTROL_PANELID) {
        //create input panel for meeting ID
        showMeetingNrDialPad("Enter the meeting ID from your calendar invite:");
    }
});

//listens to responses coming from input panels
xapi.event.on('UserInterface Message TextInput Response', (event) => {
    let regex;
    let match;
    switch (event.FeedbackId) {
        case DIALPAD_MEETINGID_ID:
            //valid meeting ID to dial?
            regex = REGEXP_NUMERIC_1TO15;
            match = regex.exec(event.Text);
            if (match !== null) {

                //save the meeting ID
                meetingID = event.Text;

                //sleep is a necessary trick to get it working with multiple touch panels to not mess up event-clears from other panels
                sleep(200).then(() => {
                    //show dial pad for the meeting pin/password
                    showMeetingPinOrPasswordDialPad("to your Zoom meeting ID: " + getMeetingIdFormatted(meetingID));
                });

            } else {
                //handle invalid meeting ID by reopening the dial pad for the meeting ID
                showMeetingNrDialPad("You typed in an invalid meeting ID. Please try again. Only digits are allowed.");
            }
            break;
        case DIALPAD_MEETINGPINORPASSWORD_ID:
            //valid meeting pin/password to dial?
            regex = REGEXP_ALPHANUMERIC_1TO15;
            match = regex.exec(event.Text);
            if (match !== null) {

                //save the meeting pin/password
                meetingPinOrPassword = event.Text;

                //sleep is a necessary trick to get it working with multiple touch panels to not mess up event-clears from other panels
                sleep(200).then(() => {
                    //create new dial pad for the  host key
                    showHostKeyDialPad("Please Note: The Host key can be found on the meeting host's Zoom profile.");
                });
            } else {
                //handle invalid meeting pin/password by reopening the dial pad for the meeting pin/password
                showMeetingPinOrPasswordDialPad("You typed in an invalid meeting password or pin. Please try again.");
            }
            break;
        case DIALPAD_HOSTKEY_ID:
            //valid host key to dial?
            regex = REGEXP_NUMERIC_6;
            match = regex.exec(event.Text);
            if (match !== null || event.Text === '') {

                //save the host key
                hostKey = event.Text;

                //dial
                xapi.command("dial", {Number: meetingID + '.' + meetingPinOrPassword + '..' + hostKey + GLOBAL_DIALPOSTFIX_URL}).catch((error) => {
                    xapi.command("dial", {Number: DEFAULT_DIALPREFIX + GLOBAL_DIALPOSTFIX_URL}).catch((error));
                    console.error(error);
                });
            } else {
                //handle invalid host key by reopening the dial pad for the host key
                showHostKeyDialPad("You typed in an invalid host key. Please try again. The host key contains 6 digits.");
            }
            break;
    }
});
