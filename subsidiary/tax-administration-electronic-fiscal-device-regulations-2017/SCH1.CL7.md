# reg 7. Test Cases
7.1 Issue of Fiscal Invoice for a Normal Receipt
A receipt and fiscal invoice must contain visible markings indicating receipt type “NORMAL”.
7.1.1. Steps
Cashier on an accredited POS selects the NORMAL type of receipt, and registers sale by: typing items, selecting items from previously made list or scanning with a bar code reader. At the end, cashier is choosing way of payment and finishing receipt.
An accredited POS is sending message to V-SDC or E-SDC. After positive invoice data verification, receipt is digitally signed, counters and totals are updated and internal data is finished.
V-SDS or E-SDC is sending back a fiscal invoice response to an accredited POS.
A fiscal invoice is issued to the customer.
7.1.2. Expected Results
A fiscal invoice is the final result of this process and can be printed or sent by SMS or email message if a customer requests it. A normal receipt is digitally signed. Internal data is stored in the data base of the Service’s system. Internal data is shown at the end of the fiscal invoice in the form of a QR code. The invoice counter is in the form 5/7NS (5-number of normal receipts/ 7-total number of receipts issued by E-SDC or V-SDC, NS — designation of normal receipt.)
7.2. Issue of Fiscal Invoice for a Refund Receipt
A receipt and fiscal invoice must contain visible markings indicating “REFUND”.
The totals on refund receipts and fiscal invoices are negative, starting with “-”.
7.2.1. Steps
Cashier on an accredited POS is selecting refund type of receipt, registering sale by: typing items, selecting items from previously made list or scanning with a bar code reader. At the end, cashier is choosing way of payment and finishing receipt.
An accredited POS is sending message to V-SDC or E-SDC. After positive invoice data verification, receipt is digitally signed, counters and totals are updated and internal data is finished.
V-SDS or E-SDC is sending back a fiscal invoice response to an accredited POS.
A fiscal invoice is issued to the customer.
7.2.2. Expected Results
A fiscal invoice is the final result of this procedure and can be printed or sent by SMS or email message if the customer is asking for it. A receipt for refund is digitally signed. Internal data is stored in the data base of the Service’s system. Internal data is present on the end of the fiscal invoice in the form of a QR code. A fiscal invoice counter is in the form 5/7NR (5-number of normal receipts for refunds/7-total number of receipts issued by E-SDC or V-SDC, NR — designation of normal receipt for refund).
7.3. Issue of Fiscal Invoice for a Copy Receipt
Receipts and fiscal invoices must contain visible markings indicating the receipt type “COPY”.
7.3.1. Steps
(a)Cashier on an accredited POS is selecting copy type of receipt. Depending on the implementation method, an accredited POS may offer to select already issued receipt from the journal memory or recall receipt number. At the end, cashier is choosing the selected receipt and producing a copy of it.
(b)An accredited POS is sending message to V-SDC or E-SDC. After positive invoice data verification, a receipt is digitally signed, counters are updated.
(c)V-SDC or E-SDC is sending back a fiscal invoice response to an accredited POS.
(d)A copy of a fiscal invoice is issued to the customer.
7.3.2. Expected Results
A copy of already issued fiscal invoice is the final result of this procedure. A fiscal invoice counter is in the form 1/9 CS (1-number of copies of normal receipts/9-total number of receipts issued by E-SDC or V-SDC, CS — designation of copy of normal receipt).
7.4. Issue of Fiscal Invoice for a Training or Pro-forma Receipt
Receipts and fiscal invoices must contain visible markings indicating the receipt type “TRAINING” or “PRO-FORMA”.
Training or pro-forma receipts and fiscal invoices are produced in the same way as normal receipts and fiscal invoices, with an exception that totals are not accounted for.
7.4.1. Steps
(a)Cashier on an accredited POS is selecting Training or Pro-forma type of the receipt, is registering sale by: typing items, selecting items from previously made list or scanning with a bar code reader. At the end, cashier is choosing way of payment and finishing receipt.
(b)An accredited POS is sending message to V-SDC or E-SDC. After positive invoice data verification, a receipt is digitally signed and counters are updated.
(c)VSDS or E-SDC is sending back a fiscal invoice response to an accredited POS.
(d)A fiscal invoice is issued.
7.4.2. Expected Results
Training or pro-forma fiscal invoice is the final result of this procedure. A fiscal invoice counter is in the form 3/8TS (3-number of receipts for training or pro-forma receipts/8-total number of receipts issued by E-SDC or V-SDC, TS — designation of receipts for training or pro-forma receipts).
7.5. Issue of Fiscal Invoice for Normal or Refund Receipt for a Business to Business Transaction
A receipt and fiscal invoice must contain visible markings of receipt type “NORMAL”, or “REFUND”.
Receipts and fiscal invoices contain business customer data, name and TIN.
7.5.1. Steps
(a)Cashier on an accredited POS is selecting receipt type, is asking customer for and inputting provided TIN, is registering sale by: typing items, selecting items from previously made list or scanning with a bar code reader. At the end, cashier is choosing way of payment and finishing receipt.
(b)An accredited POS is sending message to V-SDC or E-SDC. After positive invoice data verification, a receipt is digitally signed, counters and totals are updated and internal data is finished.
(c)VSDS or E-SDC is sending back a fiscal invoice response to an accredited POS.
(d)A fiscal invoice is issued to the customer.
7.5.2. Expected Results
A fiscal invoice is the final result of this procedure and can be printed or sent by SMS or email message if the customer is asking for it. A normal or refund receipt is digitally signed. Internal data is stored in the data base of the Service’s system. Internal data is shown at the end of the fiscal invoice in the form of a QR code. A receipt counter is in the form 5/7NS or NR number of normal receipts or normal receipts for refunds/7-total number of receipts issued by E-SDC or V-SDC, NS or NR — designation of normal receipt or normal receipt for refund).
