# reg 3. High Level Architecture of the Service’s system
[image]
This Guideline describes high level requirements for an accredited POS for all possible scenarios.
3.1. Connected Scenarios
The simplest scenario is software application (taxpayer) creates receipts, designates taxes and calls V-SDC web service to fiscalise invoices. V-SDC authenticates caller (verifies taxpayer digital certificate), performs initial validation, calculates taxes, signs receipt and returns response to a taxpayer.
A response consists of digital signature of receipt or invoice data, internal data field containing an encrypted message to the Service, digital certificate metadata, textual representation of fiscal invoice and verification URL.
The taxpayer has to generate QR code from verification URL and print textual representation of fiscal invoice and QR code. In case fiscal invoice is delivered in electronic form, verification URL should be rendered as ‘clickable’ hyperlink in email or web page.
Advantages
1.Does not require specialised hardware.
2.Accredited POS can be implemented as mobile application.
3.Existing ERPs can integrate quickly.
4.Cost of fiscalisation is reduced.
Disadvantages
1.Internet connection is required to issue fiscal invoice.
3.2. Semi-Connected Scenarios
Semi-Connected systems are designed around E-SDCs to fiscalise receipts while internet connection is not available for short or long periods of time. Some E-SDCs could be designed to work offline all the time.
In order to fiscalise a receipt in semi-connected or disconnected mode, an E-SDC receives a receipt from an accredited POS, prepares it for signing and submits the same to the secure element (implemented as smart card containing digital certificate and special applet). The secure element returns signature and internal data to the E-SDC, the E-SDC adds metadata and creates textual representation of a fiscal invoice and returns it to the accredited POS.
As in the connected scenario, a response consists of digital signature of receipt or invoice data, internal data field containing an encrypted message to the tax authority, digital certificate metadata, textual representation of the fiscal invoice and verification URL.
A taxpayer has to generate QR code from verification URL and print textual representation of the fiscal invoice and QR code. In case the fiscal invoice is delivered in electronic form, verification URL should be rendered as ‘clickable’ hyperlink in email or web page.
The E-SDC will automatically take care of audit data delivery to the Service when the device comes online or manually, using SD cards or USB Flashes.
Advantages
1.Works without internet connection.
Disadvantages
1.Requires specialised hardware.
2.Prone to physical destruction.
3.Requires network of maintenance shops.
