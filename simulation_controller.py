import logging
import json
from argparse import ArgumentParser
from typing import Dict

from swarm import VizierAgent

logging.basicConfig(level=logging.INFO)


def main():
    # Parse Command Line Arguments
    parser = ArgumentParser()
    parser.add_argument("configuration", type=str, help=".json configuration file")
    args = parser.parse_args()

    overlord = SimulationOverlord.from_config(args.configuration)
    overlord.start()
    state = {"alive": True}
    overlord.publish_all(json.dumps(state, separators=(",", ":")))
    while overlord.active:
        overlord.step()


class SimulationOverlord(VizierAgent):
    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        node_descriptor: Dict,
        bots: Dict,
    ):
        super().__init__(broker_ip, broker_port, node_descriptor)
        self.sub_to_pub = {}
        for bot in bots:
            # pylint: disable=no-member
            self.sub_to_pub[bot["sub_link"]] = bot["pub_link"]

    @classmethod
    def from_config(
        cls,
        path: str,
    ):
        # pylint: disable=arguments-differ
        with open(path, "r") as file:
            configuration = json.load(file)
            broker_ip = configuration["broker"]["ip"]
            broker_port = configuration["broker"]["port"]
            node_descriptor = configuration["node"]
            bots = configuration["bots"]
            overlord = cls(broker_ip, broker_port, node_descriptor, bots)
        return overlord

    def handle_message(self, link: str, msg: str):
        if msg == "":
            return

        logging.info("Received %s message from: %s", msg, link)

        state = json.loads(msg.decode())
        if not state["alive"]:
            self.stop()
            return
        position = state["position"]
        orientation = state["orientation"]
        print(position, orientation)
        state = {"alive": True}
        pub_link = self.sub_to_pub[link]
        self.publish(pub_link, json.dumps(state, separators=(",", ":")))


if __name__ == "__main__":
    main()