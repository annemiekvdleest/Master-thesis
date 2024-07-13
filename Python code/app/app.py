import atexit
import os
from quart import Quart, render_template, request
from connection_controller import ConnectionController, CommunicationChannel, ServerMode
from datetime import datetime
import json

app = Quart(__name__)
controller = ConnectionController(app)


@app.route("/")
async def log_view():
    cols = ["channel", "user_id", "user_message", "assistant_output", "timestamp", "processing_time"]
    return await render_template("simple.html",
                                 tables=[
                                     controller.history_df.sort_values(by="timestamp", ascending=False)[cols].to_html(
                                         classes="data")],
                                 titles=controller.history_df.columns.values)


@app.route("/start_dialogue/<button_id>", methods=["POST"])
async def start_dialogue(button_id):
    message_type = {"1": "non-empathic-starter", "2": "basic-empathy-starter", "3": "rich-empathy-starter"}.get(button_id, None)
    my_tablet_id = controller._dev_list[0]
    start_time = datetime.utcnow()
    time_string = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    msg = {"type": message_type,
           "client": {"id": my_tablet_id, "type": "TABLET"},
           "time": time_string,
           "version": "v1",
           "data": {},
           }

    await controller._handle_request(json.dumps(msg))
    return f"Dialogue: {message_type}"


@app.before_serving
async def startup():
    app.add_background_task(controller.connect_external)
    app.add_background_task(controller.connect_open_ai)

    """
       Connection as a server is established last to make sure we start receiving queries only when all connections are established
       """
    address = "ws://ws.lizz.health:5556" if controller.mode == ServerMode.PRODUCTION else "ws://ws.test.lizz.health:5556"
    app.add_background_task(controller.connect_to_socket_as_tablet, address=address)
    app.add_background_task(controller.connect_to_socket_as_server, address=address)


@app.after_serving
async def shutdown():
    while app.background_tasks:
        app.background_tasks.pop().cancel()


if __name__ == '__main__':
    if not os.path.isdir("logs"):
        os.makedirs("logs")
    atexit.register(controller.dump_history)
    print("[" + CommunicationChannel.QUART_SERVER + "] Starting Quart Server...")
    app.run(host="0.0.0.0", port=2020, debug=False)
