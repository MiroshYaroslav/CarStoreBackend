# Alerts

Terraform creates an SNS topic `<environment-name>-alerts` and subscribes
`alert_email` by email. AWS sends a confirmation message to that address; the
subscription remains pending until its confirmation link is opened.

The current CloudWatch alarm is `<environment-name>-target-5xx`: it triggers
when the ALB target group reports more than zero 5XX responses in each of two
consecutive one-minute periods. It publishes both ALARM and OK state changes to
SNS. This is a 5XX alarm, not a CPU-above-70% alarm. CPU is used by ECS target
tracking at a 60% target; Terraform does not define a separate CPU email alarm.

Capture and attach the AWS alarm email and recovery email after a real alarm
cycle. Record timestamps for first threshold breach, ALARM state, email arrival,
recovery, and OK email to estimate detection and notification latency. Do not
include email addresses, confirmation URLs, or other account secrets in shared
screenshots.

## Evidence and response time

Pending infrastructure apply, SNS confirmation, and an observed alarm/recovery
cycle. No screenshots or measured reaction times are available yet.
