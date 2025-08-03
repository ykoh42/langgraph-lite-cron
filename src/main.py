# from fastapi import FastAPI
# from langgraph_sdk import get_client
#
# from langgraph_lite_cron import crons
#
# app = FastAPI()
# app.include_router(crons.router)
#
# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
#
# client = get_client(url="")
# # Using the graph deployed with the name "agent"
# assistant_id = "agent"
# # create thread
# thread = await client.threads.create()
# print(thread)
#
# cron_job = await client.crons.create_for_thread(
#     thread["thread_id"],
#     assistant_id,
#     schedule="27 15 * * *",
#     input={"messages": [{"role": "user", "content": "What time is it?"}]},
# )
