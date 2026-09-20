"""Generator/validator script for the 15 tester accounts."""
import json

def get_15_dossiers():
    return [
        # =====================================================================
        # 5 PENDING TESTER ACCOUNTS (Standard In-Progress Turnover & Audits)
        # =====================================================================
        {
            "dossier_id": "DOS-2026-001",
            "employee_name": "Juan Dela Cruz",
            "employee_id": "EMP-94812",
            "department": "Information Technology",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Senior Specialist",
            "branch": "Taguig HQ - 24th Floor",
            "date_hired": "2022-03-15",
            "eoc_date": "2026-08-31",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_1_ASSET",
            "stage_name": "Stage 1: Asset Hand-Off & Turnover",
            "stage_step": 1,
            "current_turn_node": "IT",
            "current_turn_name": "Alex Tan (IT Clearance Lead)",
            "current_turn_role": "IT_APPROVER",
            "current_turn_action": "Verify Lenovo ThinkPad T14s serial number (20WM-0045PH) and complete corporate device wipe.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-18T08:30:00Z",
            "sample_file": "clearance_missing_it.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Alex Tan (IT Clearance Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "PENDING", "summary": "Physical laptop inspection in progress"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Locker #24 & Parking Tag Cleared"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "CLEARED", "summary": "No cash advances outstanding"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting IT hardware clearance"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Juan Dela Cruz (Employee)",
                    "date": "2026-08-31 09:15 AM",
                    "status": "COMPLETED",
                    "details": "Resignation clearance lodged via Lark Form for Taguig Corporate HQ.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "Company Laptop Hand-Off",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-02 11:30 AM",
                    "status": "IN_PROGRESS",
                    "details": "Lenovo ThinkPad T14s received at Taguig HQ reception. Serial 20WM-0045PH verified. Data sanitization in progress.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Physical Locker Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-03 02:00 PM",
                    "status": "COMPLETED",
                    "details": "Office Locker #24 padlock surrendered. 24th Floor turnstile RFID transponder deactivated.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-04 10:15 AM",
                    "status": "COMPLETED",
                    "details": "Pro-rated salary (₱32,000.00) & 13th month (₱16,500.00) audited. Net final pay: ₱48,500.00.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "Quit Claim & Waiver Sign-Off",
                    "actor": "Juan Dela Cruz (Employee)",
                    "date": "Pending Turn",
                    "status": "PENDING",
                    "details": "Awaiting IT hardware completion before final waiver execution.",
                    "icon": "fa-signature"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to BDO account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-101",
                    "author": "Alex Tan",
                    "role": "IT_APPROVER",
                    "text": "Lenovo ThinkPad T14s received at Taguig HQ reception. S/N: 20WM-0045PH. Device diagnostics healthy.",
                    "timestamp": "2026-09-02T11:45:00Z"
                },
                {
                    "id": "cmt-102",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "Net final payout confirmed at ₱48,500.00. Ready for release once IT signs off.",
                    "timestamp": "2026-09-04T10:30:00Z"
                },
                {
                    "id": "cmt-103",
                    "author": "Juan Dela Cruz",
                    "role": "REQUESTER",
                    "text": "Acknowledged and verified bank account proof. Standing by for final release.",
                    "timestamp": "2026-09-04T14:10:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-003",
            "employee_name": "Angela Soriano",
            "employee_id": "EMP-83104",
            "department": "Marketing & Brand",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Specialist / Professional",
            "branch": "Makati Central Hub",
            "date_hired": "2023-04-10",
            "eoc_date": "2026-09-22",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_1_ASSET",
            "stage_name": "Stage 1: Asset Hand-Off & Turnover",
            "stage_step": 1,
            "current_turn_node": "ADMIN",
            "current_turn_name": "Elena Cruz (Facilities Lead)",
            "current_turn_role": "ADMIN_APPROVER",
            "current_turn_action": "Collect Makati Central Hub RFID turnstile transponder and Locker #18 padlock key.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-19T09:00:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Elena Cruz (Facilities Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "MacBook Air M2 wiped & surrendered"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "PENDING", "summary": "Awaiting physical surrender of Locker #18 key"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Waiting for Admin completion"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting clearance stages"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Angela Soriano (Employee)",
                    "date": "2026-09-19 09:00 AM",
                    "status": "COMPLETED",
                    "details": "Clearance form submitted via Lark Form for Makati Central Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IT Hardware Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-19 02:00 PM",
                    "status": "COMPLETED",
                    "details": "Apple MacBook Air M2 & charger surrendered and wiped cleanly.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Physical Key Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-20 10:00 AM",
                    "status": "IN_PROGRESS",
                    "details": "Waiting on employee to deposit Locker #18 padlock key at security desk.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "Pending Turn",
                    "status": "PENDING",
                    "details": "Will initiate once Facilities confirms key surrender.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to BPI account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-301",
                    "author": "Alex Tan",
                    "role": "IT_APPROVER",
                    "text": "MacBook Air M2 diagnostics 100% clean. Passed to Facilities.",
                    "timestamp": "2026-09-19T14:15:00Z"
                },
                {
                    "id": "cmt-302",
                    "author": "Angela Soriano",
                    "role": "REQUESTER",
                    "text": "Hi Ms. Elena, I left Locker #18 padlock key with the 5th floor receptionist today.",
                    "timestamp": "2026-09-20T10:30:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-004",
            "employee_name": "Rafael Tan",
            "employee_id": "EMP-55219",
            "department": "E-Commerce Fulfillment",
            "company": "CMG Distribution Corp.",
            "unit_channel": "E-Commerce Fulfillment",
            "job_level": "Senior Associate",
            "branch": "Cebu Distribution Center",
            "date_hired": "2022-11-01",
            "eoc_date": "2026-09-24",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_2_FINANCE",
            "stage_name": "Stage 2: Finance & Payroll Audit",
            "stage_step": 2,
            "current_turn_node": "FINANCE",
            "current_turn_name": "Roberto Ong (Finance Lead)",
            "current_turn_role": "FINANCE_APPROVER",
            "current_turn_action": "Audit pro-rated September salary (₱36,500.00) and accrued 13th month bonus.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-18T10:15:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "Zebra barcode scanner surrendered"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Safety boots & uniform returned"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Auditing payroll ledger accruals"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting Finance completion"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Rafael Tan (Employee)",
                    "date": "2026-09-18 10:15 AM",
                    "status": "COMPLETED",
                    "details": "Clearance form lodged for Cebu Fulfillment Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "Warehouse Equipment Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-18 01:00 PM",
                    "status": "COMPLETED",
                    "details": "Zebra handheld inventory scanner S/N ZB-8812 surrendered and verified.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Safety Equipment",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-19 11:00 AM",
                    "status": "COMPLETED",
                    "details": "Warehouse locker cleared; steel-toe boots & hi-vis vest received.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Ledger Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-20 09:30 AM",
                    "status": "IN_PROGRESS",
                    "details": "Auditing pro-rated September earnings & 13th month accrual.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to UnionBank account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-401",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "Computation sheet generated. Auditing shift differential and overtime adjustments.",
                    "timestamp": "2026-09-20T09:45:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-005",
            "employee_name": "Beatriz Ramos",
            "employee_id": "EMP-61298",
            "department": "Human Resources",
            "company": "CMG Group of Companies",
            "unit_channel": "Corporate HQ",
            "job_level": "Specialist / Professional",
            "branch": "Taguig HQ - 24th Floor",
            "date_hired": "2021-08-16",
            "eoc_date": "2026-09-26",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_2_FINANCE",
            "stage_name": "Stage 2: Finance & Payroll Audit",
            "stage_step": 2,
            "current_turn_node": "FINANCE",
            "current_turn_name": "Roberto Ong (Finance Lead)",
            "current_turn_role": "FINANCE_APPROVER",
            "current_turn_action": "Reconcile tax withholding (BIR Form 2316) and vacation leave monetization balance.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-17T14:20:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "HRIS super-admin access disabled"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Office pedestal key returned"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Reconciling BIR 2316 and leave monetization"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting Finance completion"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Beatriz Ramos (Employee)",
                    "date": "2026-09-17 02:20 PM",
                    "status": "COMPLETED",
                    "details": "Clearance form lodged for Taguig Corporate HQ.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IAM & HRIS System Access Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-17 04:30 PM",
                    "status": "COMPLETED",
                    "details": "HRIS super-admin permissions revoked. Dell Latitude laptop wiped.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Office Pedestal Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-18 10:00 AM",
                    "status": "COMPLETED",
                    "details": "Pedestal keys returned, parking tag cleared.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Tax & Leave Monetization Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-19 01:00 PM",
                    "status": "IN_PROGRESS",
                    "details": "Auditing 8.5 unused vacation leave days monetization (₱14,200.00).",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Final payout release to BDO account and automated COE delivery.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-501",
                    "author": "Roberto Ong",
                    "role": "FINANCE_APPROVER",
                    "text": "BIR 2316 annualized tax refund computed at ₱3,450.00. Added to final pay ledger.",
                    "timestamp": "2026-09-19T14:00:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },
        {
            "dossier_id": "DOS-2026-006",
            "employee_name": "Gabriel Mendoza",
            "employee_id": "EMP-44910",
            "department": "Logistics & Supply Chain",
            "company": "CMG Logistics Philippines",
            "unit_channel": "Regional Logistics Hub",
            "job_level": "Team Lead",
            "branch": "Davao Regional Hub",
            "date_hired": "2023-02-01",
            "eoc_date": "2026-09-28",
            "employee_status": "Regular",
            "reason_for_separation": "Resignation",
            "with_clearance_already": "In Progress",
            "category": "PENDING",
            "current_stage": "STAGE_1_ASSET",
            "stage_name": "Stage 1: Asset Hand-Off & Turnover",
            "stage_step": 1,
            "current_turn_node": "ADMIN",
            "current_turn_name": "Elena Cruz (Facilities Lead)",
            "current_turn_role": "ADMIN_APPROVER",
            "current_turn_action": "Inspect Davao hub warehouse keys surrender and locker turnover.",
            "overall_status": "PENDING",
            "submitted_at": "2026-09-19T11:00:00Z",
            "sample_file": "clearance_sheet_valid.pdf",
            "sample_type": "CLEARANCE_SHEET",
            "ai_flags_count": 0,
            "flags_summary": [],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Elena Cruz (Facilities Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "No company IT assets issued"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "PENDING", "summary": "Physical locker #09 turnover pending"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Awaiting facilities clearance"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting preliminary stages"}
            },
            "escrow_details": None,
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Gabriel Mendoza (Employee)",
                    "date": "2026-09-19 11:00 AM",
                    "status": "COMPLETED",
                    "details": "Resignation clearance lodged for Davao Logistics Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IT Account Deactivation",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-19 01:30 PM",
                    "status": "COMPLETED",
                    "details": "WMS mobile scanner user deactivated. No hardware liability.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Davao Hub Facilities Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-20 11:30 AM",
                    "status": "IN_PROGRESS",
                    "details": "Locker #09 physical inspection scheduled with local depot admin.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "Pending Turn",
                    "status": "PENDING",
                    "details": "Payroll calculation queued.",
                    "icon": "fa-calculator"
                },
                {
                    "milestone": "HR Final Pay Release & COE",
                    "actor": "Grace Diaz (HR Operations)",
                    "date": "Pending Release",
                    "status": "PENDING",
                    "details": "Disbursement pending through Security Bank.",
                    "icon": "fa-money-bill-transfer"
                }
            ],
            "comments": [
                {
                    "id": "cmt-601",
                    "author": "Elena Cruz",
                    "role": "ADMIN_APPROVER",
                    "text": "Davao depot admin confirmed locker #09 contents inspected. Awaiting final gate pass.",
                    "timestamp": "2026-09-20T11:45:00Z"
                }
            ],
            "docs": [
                {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
                {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
                {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
            ]
        },

        # =====================================================================
        # 5 FOR REVIEW / FLAGGED TESTER ACCOUNTS (Discrepancy / Action Needed)
        # =====================================================================
        {
            "dossier_id": "DOS-2026-002",
            "employee_name": "Maria Clara Santos",
            "employee_id": "EMP-10294",
            "department": "Finance & Accounting",
            "company": "CMG Retail Inc.",
            "unit_channel": "Retail Stores Network",
            "job_level": "Team Lead",
            "branch": "Makati Central Hub",
            "date_hired": "2020-06-01",
            "eoc_date": "2026-09-15",
            "employee_status": "Regular",
            "reason_for_separation": "End of Contract",
            "with_clearance_already": "Yes",
            "category": "FOR_REVIEW",
            "current_stage": "STAGE_2_FINANCE",
            "stage_name": "Stage 2: Finance & Payroll Audit",
            "stage_step": 2,
            "current_turn_node": "FINANCE",
            "current_turn_name": "Roberto Ong (Finance Lead)",
            "current_turn_role": "FINANCE_APPROVER",
            "current_turn_action": "Discrepancy: ₱3,500 variance between Quitclaim draft (₱52,000) and computed payroll (₱48,500). Eligible for split escrow release.",
            "overall_status": "FLAGGED",
            "submitted_at": "2026-09-17T11:20:00Z",
            "sample_file": "quit_claim_mismatch.pdf",
            "sample_type": "QUIT_CLAIM",
            "ai_flags_count": 2,
            "flags_summary": ["FLAG_AMOUNT_MISMATCH", "FLAG_SIGNATURE_ABSENT"],
            "routing_mode": "SEQUENTIAL",
            "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
            "nodes": {
                "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "ThinkPad & IAM access revoked"},
                "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Store keys surrendered"},
                "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "FLAGGED", "summary": "₱3,500 Quitclaim vs Payroll Ledger disparity"},
                "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting Finance audit resolution"}
            },
            "escrow_details": {
                "undisputed_amount": 48500.0,
                "escrow_amount": 3500.0,
                "reason": "Disputed adapter deduction: Quitclaim stated amount (₱52,000) vs Computed Final Pay (₱48,500)",
                "status": "PENDING",
                "active": False
            },
            "timeline": [
                {
                    "milestone": "Clearance Request Lodged",
                    "actor": "Maria Clara Santos (Employee)",
                    "date": "2026-09-17 11:20 AM",
                    "status": "COMPLETED",
                    "details": "End of Contract clearance lodged via Lark Form for Makati Central Hub.",
                    "icon": "fa-file-lines"
                },
                {
                    "milestone": "IT Hardware & Cloud Turnover",
                    "actor": "Alex Tan (IT Clearance Lead)",
                    "date": "2026-09-17 03:00 PM",
                    "status": "COMPLETED",
                    "details": "ThinkPad X1 surrendered and inspected. Cloud ERP and IAM access revoked.",
                    "icon": "fa-laptop"
                },
                {
                    "milestone": "Facilities & Store Keys Turnover",
                    "actor": "Elena Cruz (Facilities Lead)",
                    "date": "2026-09-18 09:30 AM",
                    "status": "COMPLETED",
                    "details": "Office Locker #12 and Makati Central Hub physical store keys surrendered.",
                    "icon": "fa-key"
                },
                {
                    "milestone": "Finance & Payroll Computation Audit",
                    "actor": "Roberto Ong (Finance Lead)",
                    "date": "2026-09-18 02:15 PM",
                    "status": "IN_PROGRESS",
