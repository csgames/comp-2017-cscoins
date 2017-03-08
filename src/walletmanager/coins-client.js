function signMessage()
{
	var priv_key = $('#priv_key').val();
	var msg = $('#message').val();
	var sig = new KJUR.crypto.Signature({"alg": "SHA256withRSA"});
	sig.init(priv_key);
	sig.updateString(msg);

	$('#signature').text(sig.sign());
}

function generateId()
{
	var pub_key = $('#pub_key').val();
	var pubHex = KEYUTIL.getHexFromPEM(pub_key);
	
	var hasher = new jsSHA("SHA-256", "HEX");
	hasher.update(pubHex);
	
	$('#wallet_id').text(hasher.getHash("HEX"));
	
}



var coinsClient = {
	server_uri: "wss://cscoins.2017.csgames.org:8989/client",
	socket: null,
	wallet_id: null,
	public_key: null,
	private_key: null,
	transactions: [],
	my_transactions: [],
	connected: false,
	jobs_queue: [],
	current_job: null,
	job_loop: null,
	
	new_command: function(command, args) {
		return JSON.stringify({ command: command, args: args});
	},
	
	connect: function(connect_callback) {
		if(!coinsClient.socket) {
			coinsClient.socket = new WebSocket(coinsClient.server_uri);
			coinsClient.socket.onmessage = coinsClient.handle_message;
			coinsClient.socket.onopen = function() {
				coinsClient.connected = true;
				connect_callback(coinsClient.connected);
				coinsClient.start_job_loop();
			};

			coinsClient.socket.onclose = function() {
				coinsClient.connected = false;
				coinsClient.socket = null;
				connect_callback(coinsClient.connected);
				clearTimeout(coinsClient.job_loop);
			}
		}
	},
	
	disconnect: function() {
		
		
		coinsClient.socket.close();
	},
	
	start_job_loop: function() {
        coinsClient.job_loop = setTimeout(coinsClient.execute_job, 100);
        setTimeout(coinsClient.fetch_new_transactions, 5000);
    },
	
	execute_job: function() {
        if(coinsClient.current_job == null || coinsClient.current_job.terminated)
        {
            job = coinsClient.jobs_queue.shift()

            if(job) {
                coinsClient.current_job = job
                job.run(job, coinsClient.socket)
            }
        }

        coinsClient.job_loop = setTimeout(coinsClient.execute_job, 100)
    },
	
	handle_message: function(evt) {
        var jsonData = JSON.parse(evt.data)
        if(coinsClient.current_job) {
            coinsClient.current_job.onmessage(coinsClient.current_job, jsonData);
        }
    },
	
	push_job: function(run_callback, onmessage_callback) {
        var job = {
            run: function(job, websocket) {
                run_callback(job, websocket)
            },

            onmessage: function(job, data) {
                onmessage_callback(job, data)
            },

            terminated: false,
            websocket: coinsClient.socket,
            data: null,
        };

        coinsClient.jobs_queue.push(job);
    },
	
	fetch_new_transactions: function() {
		coinsClient.push_job(
			function(job, websocket) {
				if(!job.data)
				{
					job.data = { current_index: coinsClient.transactions.length, socket: websocket, transactions: [] };
				}

				websocket.send(JSON.stringify({command: 'get_transactions', args: {start: job.data.current_index, count: 100}}));
			},

			function(job, data) {
				if (data.error) {
					console.log(data.error);
					return;
				}
				
				for(var i=0; i<data.transactions.length; i++)
				{
				    addTransactionToUI(data.transactions[i]);
					job.data.transactions.push(data.transactions[i]);
				}

				if(data.transactions.length < 100)
				{
					coinsClient.transactions = coinsClient.transactions.concat(job.data.transactions);
					job.terminated = true;
					console.log("Job terminated")
					setTimeout(coinsClient.fetch_new_transactions, 5000);
					return;
				}

				job.data.current_index += data.transactions.length;
				job.run(job, job.data.socket);
			}
		);
	},
	
	signHex: function(hexData) {
			var sig = new KJUR.crypto.Signature({"alg": "SHA256withRSA"});
			sig.init(KEYUTIL.getKey(coinsClient.private_key));
			sig.updateHex(hexData);
			return sig.sign();
	},
	
	signString: function(message) {
		var sig = new KJUR.crypto.Signature({"alg": "SHA256withRSA"});
		sig.init(KEYUTIL.getKey(coinsClient.private_key));
		sig.updateString(message);
		return sig.sign();
	},
	
	register_wallet: function(walletName) {
		
		if(coinsClient.connected && coinsClient.private_key && coinsClient.public_key)
		{
			var pubHex = KEYUTIL.getHexFromPEM(coinsClient.public_key);
			var signature = coinsClient.signHex(pubHex);
			var command = coinsClient.new_command('register_wallet', {
				name: walletName,
				key: coinsClient.public_key,
				signature: signature
			});
			
			coinsClient.push_job(
				function(job, websocket) {
					websocket.send(command);
				},
				function(job, data) {
					if(data.success)
					{
						//todo wallet created succesfully
					}
				}
			);
		}
		
	},
	
	get_formatted_amount: function(amount) {
		var floatAmount = parseFloat(amount);
		floatAmount = Math.round(floatAmount*100000)/100000;
		return floatAmount.toFixed(5);
	},
	
	create_transaction: function(recipient, amount) {
        if(coinsClient.connected)
        {
			var formattedAmount = coinsClient.get_formatted_amount(amount);
			console.log(formattedAmount);
			var signatureMessage = coinsClient.wallet_id+","+recipient+","+formattedAmount;
			var signature = coinsClient.signString(signatureMessage);
			
            coinsClient.push_job(
                function (job, websocket) {
                    websocket.send(JSON.stringify({command: 'create_transaction', args: {
                            source: coinsClient.wallet_id,
                            recipient: recipient,
                            amount: amount,
							signature: signature
							}}));
                },

                function(job, data) {
                    console.log(data);
					if(data.success) {
                        //transactionSuccess(data.id);
                    } else {
                        //transactionFailed();
                    }

                    job.terminated = true;
                }
            );
        }
	},
	
	generateWalletId: function() {
		var pubHex = KEYUTIL.getHexFromPEM(coinsClient.public_key);
		var hasher = new jsSHA("SHA-256", "HEX");
		hasher.update(pubHex);
		coinsClient.wallet_id = hasher.getHash("HEX");
	}
};

function updateConnectionStatus(statusText) {
	$('#connection-status').text(statusText);
}

function updateJobStatus(jobStatus) {
	$('#job-status').text(jobStatus);
}

function hideKeys() {
	$('#wallet-public-key-field').fadeOut();
	$('#wallet-private-key-field').fadeOut();
	$('#hide-wallet-keys-btn').hide();
	$('#show-wallet-keys-btn').show();
}

function generateWalletId() {
	coinsClient.public_key = $('#wallet-public-key').val();
	coinsClient.private_key = $('#wallet-private-key').val();
	coinsClient.generateWalletId();
	$('#wallet-id').text(coinsClient.wallet_id);
}

function showKeys() {
	$('#wallet-public-key-field').fadeIn();
	$('#wallet-private-key-field').fadeIn();
	$('#hide-wallet-keys-btn').show();
	$('#show-wallet-keys-btn').hide();
}

function init_page() {
	$('#show-wallet-keys-btn').hide();
	
	updateConnectionStatus('Connecting to Central Authority Server...');
	coinsClient.connect(connect_callback);

	var elems = $('.hideable');
    elems.each(function (index){
        var state = $(this).data('state');
        if(state === 'hidden')
        {
            $(this).hide();
        }
    });
}

function connect_callback(connected) {
	var connectionStatus = 'Connected';
	
	if(!connected) {
		connectionStatus = 'Disconnected';
	}
	
	updateConnectionStatus(connectionStatus);
}

function calculateBalance() {
	if(coinsClient.public_key)
	{
		var balance = 0;
		var nbTransactions = coinsClient.transactions.length;
		for(var i=0; i<nbTransactions; i++)
		{
			var txn = coinsClient.transactions[i];
			if(txn.source == coinsClient.wallet_id)
			{
				balance -= parseFloat(txn.amount);
			}
			else if(txn.recipient == coinsClient.wallet_id)
			{
				balance += parseFloat(txn.amount);
			}
		}
		
		$('#wallet-balance').text(balance);
	}
}

function addTransactionToUI(txn) {
    var transactionsSection = $('#transactions-section');
    transactionsSection.append('<div id="txn-' +txn.id+  '" class="txn" data-txn-id="'+txn.id+'"><span class="wallet-address">'+txn.source.substr(0, 16)+'</span> to <span class="wallet-address">'+txn.recipient.substr(0, 16)+'</span> : '+txn.amount+' coin(s)</div>');
}

function showHideTransactions() {
    var transactionsSection = $('#transactions-section');
    var status = transactionsSection.data('state')

    if(status === 'hidden')
    {
        transactionsSection.fadeIn();
        transactionsSection.data('state', 'visible');
    }
    else
    {
        transactionsSection.fadeOut();
        transactionsSection.data('state', 'hidden');
    }
}

function toggleSendCoins() {
    var sendCoinsSection = $('#send-coins-section');
    if(sendCoinsSection.data('state') === 'hidden') {
        sendCoinsSection.fadeIn();
    }
}