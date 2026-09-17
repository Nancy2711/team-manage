from locust import HttpUser, task, between


class RedeemUser(HttpUser):
    """模拟一个用户：时不时查一下健康、校验兑换码、看看文档"""

    wait_time = between(1, 3)

    @task(3)
    def check_health(self):
        self.client.get("/health")

    @task(2)
    def verify_code(self):
        self.client.post("/redeem/verify", json={"code": "DEMO2026"})

    @task(1)
    def read_docs(self):
        self.client.get("/docs")
