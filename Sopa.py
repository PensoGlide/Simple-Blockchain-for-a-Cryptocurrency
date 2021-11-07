import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# Part 1 - Building a Blockchain

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block( proof = 1, previous_hash = '0')
        self.nodes = set()
        
    def create_block(self, proof, previous_hash):
        block = {'Index' : len(self.chain) + 1,
                 'Time Stamp' : str(datetime.datetime.now()),
                 'Proof' : proof,
                 'Previous Hash' : previous_hash,
                 'Transactions' : self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
        
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest() #o que está dentro do str é a condição matemática para criar a hash. Esta não pode ser simétrica, do tipo "new_proof + old_proof", não percebi o porquê
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode() #Converte o dicionário do block numa str
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['Previous Hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['Proof']
            proof = block['Proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'Sender' : sender,
                                  'Receiver' : receiver,
                                  'Amount' : amount})
        previous_block = self.get_previous_block()
        return previous_block['Index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['Length']
                chain = response.json()['Chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


################################################################
# Part 2 - Mining our Blockchain

# Create a Web App
app = Flask(__name__)
app.config[ 'JSONIFY_PRETTYPTRINT_REGULAR' ] = False

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-','')

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['Proof']
    proof = blockchain.proof_of_work(previous_proof)
    blockchain.add_transaction(sender = node_address, receiver = 'Rasco Vosa', amount = 10**3)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    response = {'Message': 'Congratulations, you just fetched some Sopa from the microwave!',
                'Index' : block['Index'],
                'Time Stamp' : block['Time Stamp'],
                'Proof' : block['Proof'],
                'Transactions' : block['Transactions'],
                'Previous Hash' : block['Previous Hash']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'Chain' : blockchain.chain,
                'Length' : len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = str(blockchain.is_chain_valid(blockchain.chain))
    if is_valid:
        response = {'Message' : 'Valid Block!'}
    else:
        response = {'Message' : 'Invalid Block!'}
    return jsonify(response) , 200

# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['Sender', 'Receiver', 'Amount']
    if not all ( key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing.', 400
    index = blockchain.add_transaction(json['Sender'], json['Receiver'], json['Amount'])
    response = {'Message' : f'This transaction will be added to block {index}.'}
    return jsonify(response), 201



################################################################
# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('Nodes')
    if nodes is None:
        return "No node.", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'Message' : 'All the nodes are now connected. The RVcoin now contains the following nodes:',
                'Total Nodes' : list(blockchain.nodes)}
    return jsonify(response), 201
    
# Replacing the chan by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'Message' : 'The chain was not the longest, so it has been replaced by the largest one.',
                    'New Chain' : blockchain.chain}
    else:
        response = {'Message' : 'The chain already is the largest one.',
                    'Actual Chain' : blockchain.chain}
    return jsonify(response) , 200






# Running the App
app.run(host = '0.0.0.0', port = 5000)