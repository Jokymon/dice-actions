# !/usr/bin/env python
# encoding: utf-8
import configparser
import paho.mqtt.client as mqtt 
import random
import json

CONFIG_INI = "config.ini"

HOST = 'localhost'
PORT = 1883



players = {}

def on_connect(client, userdata, flags, rc): 
    print('Connected') 
    mqtt.subscribe('hermes/intent/#')


def on_message(client, userdata, msg):
    def parse_slots(msg):
        print("Payload = {}".format(msg.payload))
        data = json.loads(msg.payload)
        collected_slots = {}
        for slot in data['slots']:
            slot_name = slot['slotName']
            if not slot_name in collected_slots:
                collected_slots[slot_name] = slot['value']['value']
            else:
                if type(collected_slots[slot_name])!=list:
                    collected_slots[slot_name] = [ collected_slots[slot_name] ]
                collected_slots[slot_name].append(slot['value']['value'])
        return collected_slots

    def parse_session_id(msg):
        data = json.loads(msg.payload)
        return data['sessionId']

    def say(session_id, text):
        print("Saying '{}'".format(text))
        j_out = json.dumps({'text': text, 'sessionId': session_id})
        client.publish('hermes/dialogueManager/endSession', j_out)

    global players
    slots = parse_slots(msg)
    session_id = parse_session_id(msg)
    print(slots)

    if msg.topic == 'hermes/intent/swegmann:simpleDiceThrow':
        print("Do the dice throw")
        nr_dice = int(slots.get('numberOfDice', 1))
        die_type = int(slots.get('typeOfDie', 6))
        roll = 0
        for i in range(nr_dice):
            roll += random.randint(1, die_type)

        response = "I rolled {0}".format(roll)

        say(session_id, response)

    elif msg.topic == 'hermes/intent/swegmann:createNewCountingGame':
        print("Starting a counting game")

        player_names = slots.get('playerName')
        if type(player_names)!=list:
            player_names = [ player_names ]
        players = { name: 0 for name in player_names }

        response = "I'm ready for {}".format(", ".join(player_names))

        say(session_id, response)


    elif msg.topic == 'hermes/intent/swegmann:addPoints':
        print("Adding points")

        player_name = slots.get('playerName')
        points = int(slots.get('pointsAdded'))

        if player_name in players:
            players[player_name] += points
            say(session_id, "{} now has {} points".format(player_name, players[player_name]))
        else:
            say(session_id, "I'm not currently counting for {}".format(player_name))

    elif msg.topic == 'hermes/intent/swegmann:tellScore':
        for (player, points) in sorted(players.items(), key=lambda x:x[1], reverse=True):
            say(session_id, "{}, {} points".format(player, points))


mqtt = mqtt.Client() 
if __name__ == '__main__':
    mqtt.on_connect = on_connect
    mqtt.on_message = on_message
    mqtt.connect(HOST, PORT) 
    mqtt.loop_forever()
