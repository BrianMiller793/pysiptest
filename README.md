# pysiptest

This project is under active development, and is not yet in its final form.

## Python SIP Test Framework

`pysiptest` is a Python Behave-driven framework for testing SIP scenarios.
It is designed to model a SIP client, behaving as an endpoint device.  The
tests are written to model the behavior of a specific device, allowing
emulation of devices in complex multi-caller scenarios.

### Example

    Feature: Alice Makes Calls

      Scenario: Alice calls Bob
        Given Alice uses Squirrel350 phone
        Given Bob uses Chipmunk5000 phone
        When Alice calls Bob
        Then Bob answers the phone
        And Alice and Bob talk for 10 seconds
        Then Bob hangs up the phone
        Then Alice receives BYE

      Scenario: Alice calls but Bob has DND set
        Given Alice uses Squirrel350 phone
        Given Bob uses Chipmunk5000 phone
          And Status is set to DND
        When Alice calls Bob
        Then Alice talks to voicemail for 10 seconds
        Then Alice hangs up the phone
        Then Bob has voicemail waiting

The Python step files contain functions implementing set up of the
test environment and the user actions.  This allows the test to take
action unavailable to SIPp, such as accessing APIs or databases.

Copyright &copy; 2018-2022 Brian C. Miller<br>
Open source license GNU General Public License version 3

### Motivation

Creating SIP tests modeling smart phones using `sipp` is not easy, and very
time consuming.  Registration for a receiving endpoint takes two completely
diffeent scripts, because `sipp` must first be started as a client to
register an endpoint port, and then a server to answer incoming calls.  On top
of this, `sipp` crashes for reasons unknown.

The creation of `pysiptest` allows me to simply specify a call sequence in
general terms through Behave steps.  Basing the project in Python allows
me to create a model of how a smartphone actually behaves, without needing
multiple scripts bandaged together by a shell script to work.

The RTP streams have an acceptable amount of jitter, and can echo a stream,
or replay a PCAP file.

### TODO

The project is under active development.  Refactoring is under way.  The base
libraries seem stable for now.

## RFCs

### SIP

[RFC 2543](https://datatracker.ietf.org/doc/html/rfc2543), SIP: Session Initiation Protocol, obsolete<br>
[RFC 2616](https://datatracker.ietf.org/doc/html/rfc2616), Hypertext Transfer Protocol -- HTTP/1.1<br>
[RFC 2617](https://datatracker.ietf.org/doc/html/rfc2617), HTTP Authentication: Basic and Digest Access Authentication<br>
[RFC 3261](https://datatracker.ietf.org/doc/html/rfc3261.html), SIP: Session Initiation Protocol<br>
[RFC 3262](https://datatracker.ietf.org/doc/html/rfc3262.html), Reliability of Provisional Responses in the Session Initiation Protocol (SIP)<br>
[RFC 3265](https://datatracker.ietf.org/doc/html/rfc3265.html), Session Initiation Protocol (SIP)-Specific Event Notification<br>
[RFC 3311](https://datatracker.ietf.org/doc/html/rfc3311.html), The Session Initiation Protocol (SIP) UPDATE Method<br>
[RFC 3428](https://datatracker.ietf.org/doc/html/rfc3428.html), Session Initiation Protocol (SIP) Extension for Instant Messaging<br>
[RFC 3515](https://datatracker.ietf.org/doc/html/rfc3515.html), The Session Initiation Protocol (SIP) Refer Method<br>
[RFC 3903](https://datatracker.ietf.org/doc/html/rfc3903.html), Session Initiation Protocol (SIP) Extension for Event State Publication<br>
[RFC 5626](https://datatracker.ietf.org/doc/html/rfc5626.html), Managing Client-Initiated Connections in the Session Initiation Protocol (SIP)<br>
[RFC 5839](https://datatracker.ietf.org/doc/html/rfc5839.html), An Extension to Session Initiation Protocol (SIP) Events for Conditional Event Notification<br>
[RFC 6026](https://datatracker.ietf.org/doc/html/rfc6026.html), Correct Transaction Handling for 2xx Responses to Session Initiation Protocol (SIP) INVITE Requests<br>
[RFC 6086](https://datatracker.ietf.org/doc/html/rfc6086.html), Session Initiation Protocol (SIP) INFO Method and Package Framework<br>
[RFC 6141](https://datatracker.ietf.org/doc/html/rfc6141.html), Re-INVITE and Target-Refresh Request Handling in the Session Initiation Protocol (SIP)<br>
[RFC 6878](https://datatracker.ietf.org/doc/html/rfc6878.html), IANA Registry for the Session Initiation Protocol (SIP) "Priority" Header Field<br>
[RFC 7614](https://datatracker.ietf.org/doc/html/rfc7614.html), Explicit Subscriptions for the REFER Method<br>
[RFC 7616](https://datatracker.ietf.org/doc/html/rfc7616.html), HTTP Digest Access Authentication<br>
[RFC 7621](https://datatracker.ietf.org/doc/html/rfc7621.html), A Clarification on the Use of Globally Routable User Agent URIs (GRUUs) in the SIP Event Notification Framework<br>

### Other

[RFC 3550](https://datatracker.ietf.org/doc/html/rfc3550), RTP: A Transport Protocol for Real-Time Applications, obsoletes 1889<br>
[RFC 8866](https://datatracker.ietf.org/doc/html/rfc8866), SDP: Session Description Protocol, obsoletes 4566

### Spam/Robocall Blocking, STIR/SHAKEN

[RFC 7340](https://datatracker.ietf.org/doc/html/rfc7340), Secure Telephone Identity Problem Statement and Requirements<br>
[RFC 7375](https://datatracker.ietf.org/doc/html/rfc7375), Secure Telephone Identity Threat Model (STIR)<br>
[RFC 8224](https://datatracker.ietf.org/doc/html/rfc8224), Authenticated Identity Management in the Session Initiation Protocol (SIP), obsoletes RFC 4474<br>
[RFC 8225](https://datatracker.ietf.org/doc/html/rfc8225), PASSporT: Personal Assertion Token<br>
[RFC 8226](https://datatracker.ietf.org/doc/html/rfc8226), Secure Telephone Identity Credentials: Certificates<br>
[RFC 8588](https://datatracker.ietf.org/doc/html/rfc8588), Personal Assertion Token (PaSSporT) Extension for Signature-based Handling of Asserted information using toKENs (SHAKEN)<br>
[RFC 8760](https://datatracker.ietf.org/doc/html/rfc8760), The Session Initiation Protocol (SIP) Digest Access Authentication Scheme, updates 3261
