# Автоматичне масштабування та моніторинг

## Параметри ECS

Terraform задає ECS Service Application Auto Scaling з мінімумом **1** і максимумом **4** Fargate tasks. Target tracking використовує середній `ECSServiceAverageCPUUtilization` із ціллю **60%**. Це залишає запас до насичення CPU, перш ніж система додасть capacity. Для API, що очікує на базу даних, CPU не завжди відображає черги запитів чи затримку БД; для виробничого сервісу варто також оцінити `ALBRequestCountPerTarget` або метрику latency.

Scale-out cooldown — **60 секунд**, scale-in cooldown — **300 секунд**. Cooldown — проміжок після масштабувальної дії, коли автомасштабування враховує результат попередньої дії, а не реагує на кожне коротке коливання метрики. Нульовий cooldown дозволив би швидкі повторні зміни desired count до того, як Fargate task запуститься й пройде health check; це може спричинити надмірне масштабування та нестабільні коливання. Для scale-in довший інтервал зменшує ризик прибрати capacity після короткого спаду трафіку.

Початковий `desired_count` дорівнює мінімуму, щоб після `apply` сервіс починав з однієї задачі. ECS service керується Application Auto Scaling; ручна зміна desired count під час тесту не потрібна.

## CloudWatch dashboard

Dashboard `${environment}-dashboard` має п'ять графіків із періодом 60 секунд:

1. ECS `DesiredTaskCount` і `RunningTaskCount` (Container Insights).
2. ECS `CPUUtilization`.
3. ALB `RequestCount` (сума за хвилину).
4. ALB `TargetResponseTime` зі статистикою p95.
5. ALB `HTTPCode_Target_5XX_Count`.

Під час захисту виберіть часовий інтервал тесту й позначте на знімку: початок навантаження, перетин CPU 60%, першу зміну desired/running tasks та повернення до однієї задачі. Між перетином порогу й появою нової задачі є затримка на період метрики, рішення target tracking, запуск Fargate і health checks. Scale-in відкладений довшим cooldown і має відбуватися після стабілізації попиту.

## Знімки та спостереження

Статус: Terraform-конфігурацію підготовлено, але панель ще потрібно оновити в AWS та зняти під час нового навантажувального прогону. Поточний CSV підтверджує 40 Locust users, але сам по собі не доводить, що ECS перетнув CPU target або масштабувався. Додайте сюди знімки CloudWatch і фактичні значення часу, CPU peak, desired/running counts та scale-in після тесту. Переконайтеся, що в кінці сервіс має одну задачу.
