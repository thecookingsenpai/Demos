 # This readme represents the logic of this chain

### Index
  - [The communications module](#communications.py)
  - [The federator module](#federator.py)


 ##  COMMUNICATIONS.py

 Every tx is a class that borrows communication skills
 from communication class.
 Both can (and must) be used together when an account
 want to send a tx (signed), while responses are 
 more flexible as they don't need auth.

 Here, tx contains an explicit sender note that cannot be
 counterfeit as is compared with the signature.
 The signature itself is self contained so that a tx
 contains all the data needed to be verified.

 The class communicate allows verification, signing, management 
 of previously created tx and elaboration of the tx's mode.

 ##  FEDERATOR.py

 Once this is done, the node class allows for execution and 
 reply to the tx itself. The logic behind this is to separate
 the various moments in a sort of hierarchic scale from 
 harmless to important functions.

 The node contains also the logic to be listening for txs. 
 Before being able to execute anything, however, the node
 must obtain the full blockchain and prove to be authorized 
 through the usual methods of ownership.
 Any tx which is then included in a progressive block chain
 is validated by the receiver and by the consensus protocol

 This module contains also the methods that allows peers management.
 By manually or programmatically adding (also bootstrapping) the 
 peers, a single node can connect to the whole chain through a
 single (hopefully) interaction.

 Execute data assumes the verification to be correct. Thanks to the 
 distributed file system proper of IPFS, all the nodes can
 verify in asynchronous mode the validity of the data itself. A 
 cheater is thus immediately spotted.

 Upload to IPFS is the core of the communication. Once a block is
 considered complete, the designed signers check the validation of 
 their block and, if they all agree, they upload to IPFS the chosen block.
 In case of disagreement, if all 3 disagree a new designation is done.
 If only 1 disagree a new confrontation is done excluding the possible offender.
 This process ensure that, in 2-3 iterations max, the blocks are verified.
 This is part of Proof of Integrity consensus, also called Democracy.