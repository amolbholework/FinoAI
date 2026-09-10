export interface ScamType {
  id: string
  title: string
  summary: string
  example: string
  redFlags: string[]
}

export const scamTypes: ScamType[] = [
  {
    id: 'upi-collect',
    title: 'Fake UPI collect requests',
    summary: 'A scammer sends a payment "collect" request disguised as a refund or cashback, hoping you approve it without reading.',
    example:
      'You sell an item on OLX. The "buyer" says they accidentally sent a collect request instead of a pay request, and asks you to approve it to "receive" the money — approving it actually sends money out of your account.',
    redFlags: [
      'Anyone asking you to approve a UPI request to "receive" money',
      'Urgency to approve before double-checking the app screen',
      'A buyer/seller you have never met insisting on this specific flow',
    ],
  },
  {
    id: 'phishing-link',
    title: 'Phishing links via SMS or WhatsApp',
    summary: 'A message impersonates your bank, a delivery service, or the income tax department, and links to a fake login page that steals your credentials.',
    example:
      'An SMS claims your electricity will be cut off today unless you "pay pending dues" through a link. The link opens a page that looks like a bank login but is not on the bank\'s real domain.',
    redFlags: [
      'Links in unsolicited SMS or WhatsApp messages',
      'A domain that looks close to, but not exactly, your bank\'s real site',
      'Threats of an account being blocked or a service being cut off today',
    ],
  },
  {
    id: 'fake-loan-app',
    title: 'Fake instant loan apps',
    summary: 'Unregistered lending apps offer instant loans with minimal checks, then charge hidden fees or use predatory recovery tactics.',
    example:
      'An app promises a loan approved in 5 minutes with no paperwork. After disbursing a small amount, it demands a much larger "processing fee" to release the rest, or harasses your contacts to recover money.',
    redFlags: [
      'No RBI registration or NBFC license mentioned anywhere in the app',
      'Loan approved with no income or identity verification at all',
      'Requests broad permissions to your contacts, photos, or SMS',
    ],
  },
  {
    id: 'investment-scam',
    title: '"Guaranteed return" investment schemes',
    summary: 'A scheme promises fixed, unusually high returns with "zero risk," often pushed through a Telegram or WhatsApp group.',
    example:
      'A group chat shares screenshots of huge daily profits from a "trading algorithm" and asks you to deposit funds into a personal account or a wallet, not a SEBI-registered broker.',
    redFlags: [
      'Any promise of a fixed or guaranteed return — real markets carry risk',
      'Pressure to deposit into a personal account or unfamiliar app',
      'No SEBI registration number, or one that doesn\'t check out',
    ],
  },
  {
    id: 'kyc-update',
    title: 'Fake "KYC update" calls',
    summary: 'A caller claims your bank account, SIM, or e-wallet will be blocked unless you "update KYC" immediately, then asks for OTPs or remote access.',
    example:
      'You get a call saying your SIM will be deactivated in 2 hours unless you install a remote-access app (like AnyDesk) so the "executive" can update your KYC for you.',
    redFlags: [
      'Any request to install a remote-access or screen-sharing app',
      'Any request to read out an OTP over a call',
      'Extreme urgency paired with a threat of your account being blocked',
    ],
  },
]

export interface WhatToDoStep {
  title: string
  detail: string
}

export const whatToDoIfTargeted: WhatToDoStep[] = [
  { title: 'Stop the transaction immediately', detail: 'Do not approve, forward, or read out anything else. If money has already left your account, note the time and amount.' },
  { title: 'Call your bank\'s fraud helpline', detail: 'Most banks can freeze or reverse a transaction within a short window right after it happens — the faster you call, the better the odds.' },
  { title: 'Report to the national cyber helpline', detail: 'Call 1930 or file a complaint at cybercrime.gov.in as soon as possible — this is the official Government of India channel for financial fraud.' },
  { title: 'Change your passwords and PINs', detail: 'If you shared any credentials, OTP, or installed a remote-access app, change your banking passwords and UPI PIN right away, and uninstall the app.' },
  { title: 'Screenshot everything', detail: 'Keep the message, call log, or app screen as evidence — you will need it for both the bank and the police complaint.' },
]

export const reportingChannels = {
  helplineNumber: '1930',
  portalName: 'cybercrime.gov.in',
  portalUrl: 'https://cybercrime.gov.in',
  note: 'The National Cyber Crime Reporting Portal and 1930 helpline are run by the Ministry of Home Affairs, Government of India, specifically for financial fraud and cybercrime.',
}

export interface QuizQuestion {
  id: string
  prompt: string
  options: { id: string; label: string }[]
  correctOptionId: string
  explanation: string
}

export const scamQuiz: QuizQuestion[] = [
  {
    id: 'q1',
    prompt: 'Someone calls claiming to be from your bank and asks you to read out the OTP you just received to "verify your KYC." What should you do?',
    options: [
      { id: 'a', label: 'Read it out — they already know my account details, so it must be genuine' },
      { id: 'b', label: 'Hang up. Banks never ask for an OTP over a call' },
      { id: 'c', label: 'Ask them to call back later, then read it out' },
    ],
    correctOptionId: 'b',
    explanation: 'No bank, wallet, or government agency will ever ask you to read out or share an OTP over a call. Hang up and call your bank\'s official number yourself if you\'re unsure.',
  },
  {
    id: 'q2',
    prompt: 'You receive a UPI notification asking you to approve a request to "receive ₹500 cashback." What actually happens if you enter your PIN and approve it?',
    options: [
      { id: 'a', label: 'You receive ₹500' },
      { id: 'b', label: 'Nothing happens either way' },
      { id: 'c', label: 'Money leaves your account' },
    ],
    correctOptionId: 'c',
    explanation: 'A UPI "collect" request always sends money out when approved, regardless of what the request message says. Receiving money never requires entering your PIN.',
  },
  {
    id: 'q3',
    prompt: 'An investment group promises a fixed 5% return every single week, "guaranteed, zero risk." What does this tell you?',
    options: [
      { id: 'a', label: 'It\'s a great opportunity — I should invest before it fills up' },
      { id: 'b', label: 'It\'s almost certainly a scam — no real investment guarantees fixed high returns' },
      { id: 'c', label: 'It\'s safe as long as the group has many members' },
    ],
    correctOptionId: 'b',
    explanation: 'All real investments carry risk, and returns fluctuate with the market. Any "guaranteed" high fixed return, especially pushed through a chat group, is a major red flag.',
  },
  {
    id: 'q4',
    prompt: 'You realize you just approved a fraudulent payment 3 minutes ago. What is the single most time-sensitive thing to do?',
    options: [
      { id: 'a', label: 'Post about it on social media to warn others' },
      { id: 'b', label: 'Call your bank\'s fraud helpline or 1930 immediately' },
      { id: 'c', label: 'Wait a day to see if the money is returned automatically' },
    ],
    correctOptionId: 'b',
    explanation: 'Banks and the 1930 cyber helpline have the best chance of freezing or reversing a fraudulent transaction in the first few minutes to hours. Speed matters most.',
  },
]
