# ECS autoscaling

Terraform configures ECS service target tracking on average ECS service CPU
utilization, with a 60% target, minimum one task, and maximum four tasks
(`ecs_min_capacity` / `ecs_max_capacity`). Scale-out cooldown is 60 seconds;
scale-in cooldown is 300 seconds. Cooldown is the settling interval after a
scaling action: it limits repeated decisions while new capacity starts or
traffic is being absorbed. Fargate task startup and load balancer health checks
add further delay before new tasks serve traffic.

The CloudWatch dashboard is named `<environment-name>-dashboard` and includes
ALB target p95 response time, target 5XX count, ECS service CPU and memory, and
ALB request count. ECS Container Insights is enabled. For the lab evidence,
capture the dashboard covering the load-test time window and annotate the
traffic ramp, CPU crossing the 60% target, and the ECS desired/running task
count increase (the dashboard currently does not graph task count, so use the
ECS service or Application Auto Scaling view alongside it).

## Observations

Complete after applying infrastructure and running the load test. Attach the
CloudWatch screenshot(s) here and state the test date, region, task counts,
CPU peak, and observed scale-out / scale-in times. No run data is populated in
this repository yet.
