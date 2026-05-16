"""Create research-backed ham template source and family libraries."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from final_dataset_build_utils import FINAL_BUILD_DIR, REPORTS_DIR, ensure_dirs, write_csv


TEMPLATE_DIR = FINAL_BUILD_DIR / "template_research"
SOURCES_OUT = TEMPLATE_DIR / "research_backed_ham_template_sources.csv"
FAMILIES_OUT = TEMPLATE_DIR / "research_backed_ham_template_families.csv"
RULES_OUT = TEMPLATE_DIR / "research_template_generation_rules.md"
REPORT_OUT = REPORTS_DIR / "research_template_library_report.md"
REPORT_SOURCE = Path(__file__).resolve().parents[1] / "deep-research-report (1).md"


SOURCES = [
    ("microsoft_support", "Microsoft", "authentication", "official_help", "https://support.microsoft.com/", "fixed-format SMS security codes for sign-in and unusual activity checks", "Keep terse; no account-lock threats or prize language.", "no links by default", "medium", "Deep Research report cites Microsoft Support."),
    ("google_account_help", "Google", "authentication", "official_help", "https://support.google.com/accounts/", "verification codes for recovery, 2-Step Verification, account creation, and sign-in checks", "Code-only user-action flows are safest.", "no links by default", "medium", "Deep Research report cites Google Account Help."),
    ("apple_support", "Apple", "authentication", "official_help", "https://support.apple.com/", "six-digit verification codes for trusted phone numbers and sign-ins", "Minimal non-promotional code messages only.", "no links", "medium", "Deep Research report cites Apple Support."),
    ("amazon_customer_service", "Amazon", "authentication", "official_help", "https://www.amazon.com/gp/help/customer/", "2-Step Verification security codes by SMS", "Avoid order/refund scare language in OTP family.", "no links", "medium", "Deep Research report cites Amazon Customer Service."),
    ("paypal_help", "PayPal", "authentication", "official_help", "https://www.paypal.com/help/", "security codes and narrow activity confirmations", "Interactive replies must stay narrow and non-scammy.", "no links by default", "medium", "Deep Research report cites PayPal Help."),
    ("bdo_security", "BDO", "banking", "official_security", "https://www.bdo.com.ph/", "unknown-device notices, transfer alerts, unusual transaction notices", "No OTP/password requests; PH finance no-link default.", "no links", "high", "Deep Research report cites BDO."),
    ("bpi_alerts", "BPI", "banking", "official_security", "https://www.bpi.com.ph/", "card transaction SMS alerts and Secure SMS/device-registration flows", "Avoid deactivation threats and random verification links.", "no links", "high", "Deep Research report cites BPI."),
    ("gcash_help", "GCash", "ewallet", "official_help", "https://help.gcash.com/", "login OTPs and device-registration/security warnings", "Favor OTP/device security over broad SMS confirmations.", "no links", "high", "Deep Research report cites GCash Help Center."),
    ("maya_support", "Maya", "ewallet", "official_help", "https://support.maya.ph/", "six-digit OTP sent by text when app asks for it", "App-directed, code-centric; no unlock-account links.", "no links", "medium", "Deep Research report cites Maya."),
    ("globe_help", "Globe", "telecom", "official_help", "https://www.globe.com.ph/help", "OTPs for critical transactions, SIM confirmations, outage advisories", "Globe-like synthetic ham should not contain links.", "no links", "medium", "Deep Research report cites Globe Help."),
    ("smart_help", "Smart", "telecom", "official_help", "https://smart.com.ph/help", "4-digit GigaLife and billing/carrier-billing OTPs", "Tie OTP to concrete action; avoid prize claims.", "no links", "medium", "Deep Research report cites Smart Help."),
    ("ups_tracking", "UPS", "delivery", "official_help", "https://www.ups.com/", "shipment-status notification texts and tracking updates", "Payment variants only with strong shipment context.", "official account/channel only", "medium", "Deep Research report cites UPS."),
    ("usps_text_tracking", "USPS", "delivery", "official", "https://www.usps.com/text-tracking/welcome.htm", "user-requested text tracking updates", "No address-fix or payment-demand messages.", "no links by default", "medium", "Deep Research report cites USPS Text Tracking."),
    ("dhl_fraud_awareness", "DHL", "delivery", "official_security", "https://www.dhl.com/", "customs-payment notices with shipment context", "Visually close to smishing; keep sparse.", "official channels only", "low", "Deep Research report cites DHL fraud awareness/payment guidance."),
    ("va_vetext", "VA VEText", "appointment", "public_service", "https://www.va.gov/", "appointment reminders and optional check-in notices", "Minimize health details and never request payment.", "official account/channel only", "low", "Deep Research report cites VA.gov."),
    ("nhs_govuk", "NHS/GOV.UK", "appointment", "public_service", "https://www.gov.uk/", "appointment reminders and app-first health messages with SMS fallback", "Calm logistics only; avoid sensitive medical detail.", "no links by default", "low", "Deep Research report cites GOV.UK/NHS."),
    ("uscis_g1145", "USCIS", "government", "public_service", "https://www.uscis.gov/", "application or petition acceptance text/email notices", "Dry acknowledgment only; no fees or threats.", "official account/channel only", "low", "Deep Research report cites USCIS G-1145."),
]


FAMILIES = [
    ("fixed_format_big_brand_otp_microsoft", "microsoft_support", "fixed_format_big_brand_otp", "authentication", "big_tech", "high-volume but brand-capped OTP", "medium", 20, 10, "Microsoft security code: {OTP}. Use this to verify your sign-in.", "OTP", "", "Microsoft", "False", "no links", "Do not over-paraphrase brand OTPs.", "account will be locked|claim prize|click now|password", "Microsoft documents SMS security codes; use conservative code-only style.", "approved"),
    ("fixed_format_big_brand_otp_google", "google_account_help", "fixed_format_big_brand_otp", "authentication", "big_tech", "high-volume but brand-capped OTP", "medium", 20, 10, "Google verification code: {OTP}. Enter this code to continue.", "OTP", "", "Google", "False", "no links", "Tie to user action; no threats.", "account will be locked|claim prize|click now|password", "Google help documents SMS verification codes for account workflows.", "approved"),
    ("fixed_format_big_brand_otp_apple", "apple_support", "fixed_format_big_brand_otp", "authentication", "big_tech", "high-volume but brand-capped OTP", "medium", 20, 10, "Apple Account verification code: {OTP}. Enter this code to sign in.", "OTP", "", "Apple", "False", "no links", "Minimal, code-focused.", "account will be locked|claim prize|click now|password", "Apple support centers on verification codes for trusted numbers.", "approved"),
    ("fixed_format_big_brand_otp_amazon", "amazon_customer_service", "fixed_format_big_brand_otp", "authentication", "big_tech", "high-volume but brand-capped OTP", "medium", 20, 10, "Amazon security code: {OTP}. Enter this code to continue signing in.", "OTP", "", "Amazon", "False", "no links", "Avoid order/refund scare language.", "account will be locked|claim prize|click now|password", "Amazon help documents 2-Step Verification codes.", "approved"),
    ("fixed_format_big_brand_otp_paypal", "paypal_help", "fixed_format_big_brand_otp", "authentication", "fintech", "high-volume but brand-capped OTP", "medium", 20, 10, "PayPal security code: {OTP}. Enter this code on the screen.", "OTP", "", "PayPal", "False", "no links", "Keep reply/activity variants separate and sparse.", "account will be locked|claim prize|click now|password", "PayPal help documents SMS security codes entered on-screen.", "approved"),
    ("generic_account_verification_app", "paypal_help", "generic_account_verification", "authentication", "generic_service", "generic app/account OTP", "medium", 100, 20, "{BRAND} verification code: {OTP}. Enter this code in the app to continue.", "BRAND|OTP", "", "Your account|Your app|Your service|PayPal|Maya|GCash", "False", "no links", "No threats or links.", "account will be locked|claim prize|click now|password", "Cross-source rule: context first, code second.", "approved"),
    ("generic_account_security_code", "google_account_help", "generic_account_verification", "authentication", "generic_service", "generic screen-entered code", "medium", 100, 20, "{BRAND} security code: {OTP}. Enter this code on the screen.", "BRAND|OTP", "", "Your account|Your app|Your service|PayPal|Maya|GCash", "False", "no links", "No credential collection.", "send your OTP|share your OTP|reply with your PIN", "Official OTP flows ask the user to enter code in app/site.", "approved"),
    ("generic_account_otp_continue", "gcash_help", "generic_account_verification", "authentication", "generic_service", "generic OTP with anti-sharing reminder", "medium", 100, 20, "{BRAND}: Use OTP {OTP} to continue your request. Never share this code.", "BRAND|OTP", "", "Your account|Your app|Your service|PayPal|Maya|GCash", "False", "no links", "Protective anti-sharing wording only.", "send your OTP|share your OTP|reply with your PIN", "GCash/Maya guidance supports never-share-code notices.", "approved"),
    ("risk_signin_new_device", "bdo_security", "risk_based_signin_device_alert", "account_security", "financial", "new-device account alert", "medium", 100, 15, "{BRAND} Alert: A sign-in from a new device was detected for your account ending {LAST4}.", "BRAND|LAST4", "", "BDO|BPI|GCash|Maya|Your bank|Your e-wallet", "False", "no links", "Neutral security notification; official channels only.", "verify now or lose access|account will be locked|password", "BDO/BPI/GCash/Maya sources document device/security notices.", "approved"),
    ("risk_phone_registration_otp", "gcash_help", "risk_based_signin_device_alert", "account_security", "ewallet", "phone/device registration verification", "medium", 100, 15, "{BRAND}: For your safety, use OTP {OTP} to verify your phone registration request.", "BRAND|OTP", "", "BDO|BPI|GCash|Maya|Your bank|Your e-wallet", "False", "no links", "No OTP sharing request.", "send your OTP|share your OTP|password", "GCash device-registration guidance supports this style.", "approved"),
    ("risk_device_registration_time", "bpi_alerts", "risk_based_signin_device_alert", "account_security", "financial", "device registration notice", "medium", 100, 15, "{BRAND}: Device registration request received at {TIME}. If this was not you, use official support channels.", "BRAND|TIME", "", "BDO|BPI|GCash|Maya|Your bank|Your e-wallet", "False", "no links", "Avoid lock/suspension threats.", "account will be locked|verify now or lose access|click this link", "BPI/BDO sources support neutral device/security alerts.", "approved"),
    ("bank_card_used", "bpi_alerts", "bank_card_transaction_alert", "banking", "financial", "card transaction alert", "high", 100, 20, "{BRAND} Alert: Your card ending {LAST4} was used for PHP {AMOUNT} at {MERCHANT} on {DATE_TIME}.", "BRAND|LAST4|AMOUNT|MERCHANT|DATE_TIME", "", "BDO|BPI|Metrobank|Your bank", "False", "no links", "Neutral alert; no credential request.", "account will be suspended|send your OTP|CVV|password", "BPI documents card transaction alerts.", "approved"),
    ("bank_debit_ref", "bdo_security", "bank_card_transaction_alert", "banking", "financial", "debit transaction alert", "high", 100, 20, "{BRAND}: Debit of PHP {AMOUNT} from acct ending {LAST4}. Ref: {REF_NUM}.", "BRAND|AMOUNT|LAST4|REF_NUM", "", "BDO|BPI|Metrobank|Your bank", "False", "no links", "PH finance no-link default.", "account will be suspended|send your OTP|CVV|password", "BDO/BPI sources support transaction monitoring alerts.", "approved"),
    ("bank_transfer_requested", "bdo_security", "bank_card_transaction_alert", "banking", "financial", "transfer request alert", "high", 100, 20, "{BRAND}: Transfer of PHP {AMOUNT} to another local bank was requested at {TIME}. Ref: {REF_NUM}.", "BRAND|AMOUNT|TIME|REF_NUM", "", "BDO|BPI|Metrobank|Your bank", "False", "no links", "No threat follow-up.", "account will be suspended|send your OTP|CVV|password", "BDO source documents transfer alert texts.", "approved"),
    ("ewallet_login_otp", "gcash_help", "ewallet_login_verification", "ewallet", "financial", "e-wallet login OTP", "medium", 100, 20, "{BRAND} OTP: {OTP}. Use this to verify your login. Never share this code.", "BRAND|OTP", "", "GCash|Maya|Your e-wallet", "False", "no links", "No reward bait.", "claim prize|win reward now|send your OTP|share your OTP", "GCash/Maya sources document SMS OTPs.", "approved"),
    ("ewallet_app_code", "maya_support", "ewallet_login_verification", "ewallet", "financial", "e-wallet app verification code", "medium", 100, 20, "{BRAND} verification code: {OTP}. Enter this code in the app to continue.", "BRAND|OTP", "", "GCash|Maya|Your e-wallet", "False", "no links", "Short and app-directed.", "claim prize|win reward now|send your OTP|share your OTP", "Maya support documents app-requested OTPs.", "approved"),
    ("ewallet_phone_registration", "gcash_help", "ewallet_login_verification", "ewallet", "financial", "e-wallet phone registration", "medium", 100, 20, "{BRAND}: Phone registration request received. Use OTP {OTP} only inside the app.", "BRAND|OTP", "", "GCash|Maya|Your e-wallet", "False", "no links", "No person-to-person code sharing.", "send your OTP|share your OTP|password", "GCash security/device-registration guidance supports this style.", "approved"),
    ("telecom_bill_payment_otp", "globe_help", "telecom_otp_service_advisory", "telecom", "telecom", "bill payment OTP", "medium", 100, 20, "{BRAND} OTP {OTP} for bill payment. Do not share this code.", "BRAND|OTP", "", "Globe|Smart|Your telecom provider", "False", "no links", "Avoid prize/points bait.", "free spins|claim prize|bit.ly|tinyurl", "Globe/Smart sources document OTPs for critical transactions.", "approved"),
    ("telecom_signup_otp", "smart_help", "telecom_otp_service_advisory", "telecom", "telecom", "app sign-up OTP", "medium", 100, 20, "{BRAND} OTP: {OTP}. Enter this code to complete your app sign-up.", "BRAND|OTP", "", "Globe|Smart|Your telecom provider", "False", "no links", "Tie to concrete user action.", "free spins|claim prize|bit.ly|tinyurl", "Smart documents GigaLife sign-up OTPs.", "approved"),
    ("telecom_network_advisory", "globe_help", "telecom_otp_service_advisory", "telecom", "telecom", "network issue advisory", "medium", 100, 20, "{BRAND} Advisory: We are resolving a network issue in {LOCATION}. Estimated restoration is {TIME}.", "BRAND|LOCATION|TIME", "", "Globe|Smart|Your telecom provider", "False", "no links", "Operational advisory only.", "free spins|claim prize|bit.ly|tinyurl", "Globe source supports network-outage advisories.", "approved"),
    ("telecom_load_active", "smart_help", "telecom_otp_service_advisory", "telecom", "telecom", "load promo active confirmation", "medium", 100, 20, "{BRAND}: Your load promo is active until {DATE_TIME}. Ref: {REF_NUM}.", "BRAND|DATE_TIME|REF_NUM", "", "Globe|Smart|Your telecom provider", "False", "no links", "Avoid spam-like promo wording.", "free spins|claim prize|bit.ly|tinyurl", "Telecom service confirmations add diversity without links.", "approved"),
    ("delivery_out_for_delivery", "ups_tracking", "delivery_tracking_update", "delivery", "logistics", "out-for-delivery update", "medium", 100, 20, "{BRAND}: Package {TRACKING_NUM} is out for delivery today.", "BRAND|TRACKING_NUM", "", "UPS|USPS|DHL|J&T Express|LBC|Your courier", "False", "no links", "Status-centered and low pressure.", "small fee|address fix|bit.ly|tinyurl", "UPS/USPS/DHL sources support tracking status texts.", "approved"),
    ("delivery_delivered", "usps_text_tracking", "delivery_tracking_update", "delivery", "logistics", "delivered status", "medium", 100, 20, "{BRAND} Tracking {TRACKING_NUM}: Delivered at {TIME}.", "BRAND|TRACKING_NUM|TIME", "", "UPS|USPS|DHL|J&T Express|LBC|Your courier", "False", "no links", "No address-fix links.", "small fee|address fix|bit.ly|tinyurl", "USPS Text Tracking supports delivered updates.", "approved"),
    ("delivery_scheduled", "ups_tracking", "delivery_tracking_update", "delivery", "logistics", "scheduled delivery", "medium", 100, 20, "{BRAND}: Your parcel with ref {REF_NUM} is scheduled for delivery on {DATE}.", "BRAND|REF_NUM|DATE", "", "UPS|USPS|DHL|J&T Express|LBC|Your courier", "False", "no links", "No small-fee links.", "small fee|address fix|bit.ly|tinyurl", "Carrier sources support neutral schedule updates.", "approved"),
    ("customs_duties_due", "dhl_fraud_awareness", "customs_or_fee_request_low_volume", "delivery", "logistics", "sparse customs/duties notice", "low", 30, 10, "{BRAND}: Duties and tax are due for shipment {TRACKING_NUM} from {MERCHANT}. Complete payment through your official account.", "BRAND|TRACKING_NUM|MERCHANT", "", "DHL Express|UPS", "False", "official account only", "Very low volume because visually close to smishing.", "urgent action required|bit.ly|tinyurl|account will be locked", "DHL/UPS sources allow shipment-specific payment flows.", "approved"),
    ("customs_import_charges", "ups_tracking", "customs_or_fee_request_low_volume", "delivery", "logistics", "sparse import charge notice", "low", 30, 10, "{BRAND}: Shipment {TRACKING_NUM} has import charges due. Review details through official {BRAND} channels.", "BRAND|TRACKING_NUM", "", "DHL Express|UPS", "False", "official channels only", "Very low volume; no links.", "urgent action required|bit.ly|tinyurl|account will be locked", "UPS/DHL official guidance supports official-channel payment handling.", "approved"),
    ("appointment_tomorrow", "va_vetext", "appointment_reminder", "appointment", "public_service", "appointment reminder", "low", 60, 20, "{BRAND} Reminder: You have an appointment tomorrow at {TIME}.", "BRAND|TIME", "", "VA|NHS|Clinic|Your clinic", "False", "no links by default", "No medical details.", "payment demand|lab result|diagnosis|urgent action required", "VA/NHS sources support sparse appointment reminders.", "approved"),
    ("appointment_date", "nhs_govuk", "appointment_reminder", "appointment", "public_service", "appointment reminder with date", "low", 60, 20, "{BRAND} Reminder: You have an appointment on {DATE} at {TIME}. Please attend as scheduled.", "BRAND|DATE|TIME", "", "VA|NHS|Clinic|Your clinic", "False", "no links by default", "Calm logistical wording.", "payment demand|lab result|diagnosis|urgent action required", "NHS/GOV.UK supports appointment reminder styles.", "approved"),
    ("appointment_account_details", "va_vetext", "appointment_reminder", "appointment", "public_service", "account detail reminder", "low", 60, 20, "{BRAND}: Appointment reminder for {DATE_TIME}. Check your account for details.", "BRAND|DATE_TIME", "", "VA|NHS|Clinic|Your clinic", "False", "official account only", "No sensitive clinic/diagnosis details.", "payment demand|lab result|diagnosis|urgent action required", "VA guidance minimizes sensitive appointment details.", "approved"),
    ("gov_application_accepted", "uscis_g1145", "government_application_acknowledgment", "government", "public_service", "application accepted", "low", 50, 15, "{BRAND}: We accepted your application on {DATE}. Check your case status through your official account.", "BRAND|DATE", "", "USCIS|SSS|PhilHealth|Government Service", "False", "official account only", "No fees, threats, or random links.", "urgent action required|fee|account will be locked|bit.ly", "USCIS G-1145 supports application acceptance notices.", "approved"),
    ("gov_reference_received", "uscis_g1145", "government_application_acknowledgment", "government", "public_service", "reference received", "low", 50, 15, "{BRAND}: Your application reference {REF_NUM} was received on {DATE}.", "BRAND|REF_NUM|DATE", "", "USCIS|SSS|PhilHealth|Government Service", "False", "no links", "Dry administrative wording.", "urgent action required|fee|account will be locked|bit.ly", "Government/public-service sources support receipt notices.", "approved"),
    ("gov_service_recorded", "uscis_g1145", "government_application_acknowledgment", "government", "public_service", "service request recorded", "low", 50, 15, "{BRAND}: Your service request {REF_NUM} has been recorded.", "BRAND|REF_NUM", "", "USCIS|SSS|PhilHealth|Government Service", "False", "no links", "No threats or payment demand.", "urgent action required|fee|account will be locked|bit.ly", "Government-style acknowledgments are dry and administrative.", "approved"),
]


SOURCE_COLUMNS = ["source_id", "company_or_service", "source_type", "trust_level", "source_url", "supported_message_styles", "risk_notes", "url_policy", "recommended_volume_level", "notes"]
FAMILY_COLUMNS = ["template_family_id", "source_id", "family_name", "service_category", "institution_type", "recommended_use", "volume_level", "max_family_count", "max_variant_count", "template_text", "required_slots", "optional_slots", "allowed_brands", "url_allowed", "url_policy", "risk_notes", "banned_phrases", "source_basis_summary", "template_status"]


def main() -> None:
    ensure_dirs()
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    sources = pd.DataFrame(SOURCES, columns=SOURCE_COLUMNS)
    families = pd.DataFrame(FAMILIES, columns=FAMILY_COLUMNS)
    write_csv(sources, SOURCES_OUT)
    write_csv(families, FAMILIES_OUT)
    RULES_OUT.write_text(
        "\n".join(
            [
                "# Research Template Generation Rules",
                "",
                "These templates are style-inspired from the Deep Research report, not copied official SMS datasets.",
                "",
                "- Use fake/generated slot values only.",
                "- Generate ham only; do not generate synthetic smishing.",
                "- Keep big-brand OTP wording stable and cap each brand family.",
                "- Prefer no-link templates, especially for Philippine finance and telecom.",
                "- Keep customs/payment-like logistics messages sparse and shipment-specific.",
                "- Reject scam-like urgency, gambling/free-spin language, account-lock threats, shortened URLs, and requests to share OTP/PIN/password/CVV.",
                "- Produce `message_raw` with filled values and `message_clean` with privacy placeholders.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    counts = families["family_name"].value_counts().to_dict()
    lines = [
        "# Research-Backed Template Library Report",
        "",
        f"- Deep Research source file: `{REPORT_SOURCE}`",
        f"- Source rows created: {len(sources)}",
        f"- Template families created: {len(families)}",
        "",
        "The library uses the Deep Research report as a style guide only. It does not scrape websites, copy user-submitted messages, or claim synthetic ham rows are collected SMS.",
        "",
        "## Families",
        "",
        "| Family | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {k} | {v} |" for k, v in sorted(counts.items()))
    lines.extend(["", f"- Sources CSV: `{SOURCES_OUT}`", f"- Families CSV: `{FAMILIES_OUT}`", f"- Rules: `{RULES_OUT}`"])
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Research template sources created: {len(sources)}")
    print(f"Research template families created: {len(families)}")
    print(f"Wrote: {SOURCES_OUT}")
    print(f"Wrote: {FAMILIES_OUT}")
    print(f"Report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
