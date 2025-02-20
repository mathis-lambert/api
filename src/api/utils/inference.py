class InferenceUtils:
    @staticmethod
    def format_messages(prompt: str, input: str, history: list) -> list:
        messages = []

        if prompt:
            messages.append({"role": "system", "content": prompt})

        if history:
            for entry in history:
                messages.append({"role": entry["role"], "content": entry["content"]})

        messages.append({"role": "user", "content": input})

        return messages

    @staticmethod
    def format_response(response: str, job_id: str) -> dict:
        return {"response": response, "job_id": job_id}
