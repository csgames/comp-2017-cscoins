function signMessage() {
	var priv_key = $('#priv_key').val();
	var msg = $('#message').val();
	var sig = new KJUR.crypto.Signature({"alg": "SHA256withRSA"});
	sig.init(priv_key);
	sig.updateString(msg);

	$('#signature').text(sig.sign());
}

function generateId() {
	var pub_key = $('#pub_key').val();
	var pubHex = KEYUTIL.getHexFromPEM(pub_key);
	
	var hasher = new jsSHA("SHA-256", "HEX");
	hasher.update(pubHex);
	
	$('#wallet_id').text(hasher.getHash("HEX"));
}



var coinsClient = {
	server_uri: "wss://cscoins.2017.csgames.org:8989/client",
	//server_uri: "ws://localhost:8989/client",
	socket: null,
	wallet_id: null,
	public_key: null,
	private_key: null,
	transactions: [],
	connected: false,
	jobs_queue: [],
	current_job: null,
	job_loop: null,
	support_storage: false,
	
	new_command: function(command, args) {
		return JSON.stringify({ command: command, args: args});
	},
	
	connect: function(connect_callback) {

		if(!coinsClient.socket) {
			coinsClient.loadKeysFromStorage();
			
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
				    console.log(data);
					if(data.error) {
						walletRegistrationFailed(data.error);
					}
					else {
					    walletRegistrationSuccess();
					}

					job.terminated = true;
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
					if(!data.error) {
                        transactionSuccess(data.id);
                    } else {
                        transactionFailed(data.error);
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
	},
	
	loadKeysFromStorage: function () {
		if(!coinsClient.support_storage) {
			console.log("HTML5 Storage not supported !");
			return;
		}
		
		var privKey = localStorage.getItem('wallet-private-key');
		var pubKey = localStorage.getItem('wallet-public-key');
		
		if(privKey && pubKey) {
			coinsClient.public_key = pubKey;
			coinsClient.private_key = privKey;
			$('#wallet-public-key').val(pubKey)
			$('#wallet-private-key').val(privKey);
			coinsClient.generateWalletId();
			//Hide wallet keys from
			$('#wallet-id').text(coinsClient.wallet_id);
			hideKeys();
		}
	},
	
	saveKeysToStorage: function () {
		if(!coinsClient.support_storage)
		{
			console.log("HTML5 Storage not supported !");
			return;
		}
		
		if(coinsClient.public_key && coinsClient.private_key) {
			localStorage.setItem('wallet-private-key', coinsClient.private_key);
			localStorage.setItem('wallet-public-key', coinsClient.public_key);
		}
	},
};

function updateConnectionStatus(connectionStatus) {
	
	//hidding all span
	$('#connection-status span').each(function(index, value){
		$(value).hide();
	});
	
	$('#connection-status-'+connectionStatus).fadeIn();
}

function updateJobStatus(jobStatus) {
	$('#job-status').text(jobStatus);
}

function hideKeys() {
	$('#wallet-keys-form').fadeOut();
	$('#hide-wallet-keys-btn').hide();
	$('#show-wallet-keys-btn').show();
}

function generateWalletId() {
	coinsClient.public_key = $('#wallet-public-key').val();
	coinsClient.private_key = $('#wallet-private-key').val();
	coinsClient.generateWalletId();
	coinsClient.saveKeysToStorage();
	$('#wallet-id').text(coinsClient.wallet_id);

    if(coinsClient.transactions.length > 0)
    {
        $('#transactions-container .txn').remove();
        var nb = coinsClient.transactions.length;
        for(var i=0; i<nb; i++) {
            addTransactionToUI(coinsClient.transactions[i]);
        }
    }
}

function showKeys() {
	$('#wallet-keys-form').fadeIn();
	$('#hide-wallet-keys-btn').show();
	$('#show-wallet-keys-btn').hide();
}

function init_page() {
	var elems = $('.hideable');
    elems.each(function (index){
        var state = $(this).data('state');
        if(state === 'hidden')
        {
            $(this).hide();
        }
    });
	
	
	coinsClient.support_storage = support_storage();
	coinsClient.connect(connect_callback);
}

function support_storage() {
	try {
		return 'localStorage' in window && window['localStorage'] !== null;
	} catch (e) {
		return false;
	}
}

function connect_callback(connected) {
	var connectionStatus = 'connected';
	
	if(!connected) {
		connectionStatus = 'disconnected';
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
    var transactionsSection = $('#transactions-container');
	var template = $('#template #txn');
	
	var txnElement = template.clone();
	
	txnElement.find('#txn-id').text(txn.id);
	
	txnElement.find('#source-address').text(txn.source.substr(0, 32));
	txnElement.find('#source-address').attr('title', txn.source);
	
	if(txn.source === coinsClient.wallet_id)
	{
		txnElement.find('#source-address').attr('class', 'my-wallet-id');
	}
	
	txnElement.find('#recipient-address').text(txn.recipient.substr(0, 32));
	txnElement.find('#recipient-address').attr('title', txn.recipient);
	
	if(txn.recipient === coinsClient.wallet_id)
	{
		txnElement.find('#recipient-address').attr('class', 'my-wallet-id');
	}
	
	txnElement.find('#txn-amount').text(txn.amount);
	
	txnElement.prop('id', 'txn-'+txn.id);
	transactionsSection.append(txnElement);
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
	var sendCoinsForm = $('#send-coins-form');
	
	resetSendCoinStatus();
    sendCoinsSection.show();
    sendCoinsSection.data('state','visible');

	sendCoinsForm.show();
	sendCoinsForm.data('state','visible');
}

function resetSendCoinStatus()
{
	$('#transaction-information span.label').each(function (index, value){
		var label = $(value);
		label.hide();
		label.data('state', 'hidden');
	});
}

function transactionSuccess(txnId) {
	$('#send-coins-toggle').fadeIn();
	
	resetSendCoinStatus();
	var successLabel = $('#send-coin-success');
	successLabel.text(successLabel.text().split(':')[0] + ' : id = ' + txnId);
	successLabel.fadeIn();
}

function transactionFailed(errorMessage) {
	$('#send-coins-toggle').fadeIn();
	
	resetSendCoinStatus();
	
	var errorLabel = $('#send-coin-error');
	errorLabel.text(errorLabel.text().split(':')[0] + ' : ' + errorMessage);
	errorLabel.fadeIn();
}

function send_coins() {
	var recipient = $('#transaction-recipient').val();
	var amount = $('#transaction-amount').val();
	
	var sendCoinsForm = $('#send-coins-form');
	sendCoinsForm.fadeOut();
	sendCoinsForm.data('state', 'hidden');
	
	$('#send-coin-pending').fadeIn();
	
	coinsClient.create_transaction(recipient, amount);
}

function register_wallet() {
    resetWalletRegistrationStatus();
    generateWalletId();
    var walletName = window.prompt("What is the name of this wallet ?", "Unknown");
    coinsClient.register_wallet(walletName);
    $('#wallet-registration-pending').show();
}

function resetWalletRegistrationStatus()
{
	$('#wallet-registration-information span.label').each(function (index, value){
		var label = $(value);
		label.hide();
		label.data('state', 'hidden');
	});
}

function walletRegistrationFailed(errorMessage) {
    resetWalletRegistrationStatus();
    var errorLabel = $('#wallet-registration-error');
	errorLabel.text(errorLabel.text().split(':')[0] + ' : ' + errorMessage);
	errorLabel.fadeIn();
}

function walletRegistrationSuccess() {
    resetWalletRegistrationStatus()
    $('#wallet-registration-success').fadeIn();
}