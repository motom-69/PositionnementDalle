import tensorflow as tf
assert hasattr(tf, "function") # Be sure to use tensorflow 2.0
import os
import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,AutoMinorLocator)
import time
from sklearn.utils import shuffle
import keras.backend as K

#### SETING-UP ######
# Model configuration
NbEpochs=50
NbLayerHidden=4
NbCellLayer=50
ActivationType="elu" #data value between -1 and 1
BATCH_SIZE = 32
Optimizer='adadelta' #'adam'
# To avoid overfitting
LayerDropout=False #True
LayerDropoutValue=0.05
L2Regularization=True
L2RegularizationValue=0.01
# For plot curve name info only (how input has been generated) No infuence here
NbDalleVoisineMax=15
NormalIndicator=True
# Running type
restart=False #True #if True, load weight from previous study
optimization=True
# Name of file containing features
input_file='inputv5_between-1and1_Max6Min-6_noshuffle.txt'
target_file='targetv5_between-1and1_Max6Min-6_noshuffle.txt'
#### SETING-UP ######

# Create tensorflow tensors from feature files
Inputs=[]
Targets=[]
if os.path.exists(input_file) and os.path.exists(target_file):
	fa=open(input_file,'r')
	fb=open(target_file,'r')
	txta=fa.readlines()
	txtb=fb.readlines()
	print('Length of input files -> ',len(txta))
	print('Length of target files -> ',len(txtb))
	fa.close()
	fb.close()
	
	limit=min(len(txta),len(txtb)) # if crash during feature files generation, only common lines are taken
	
	for i in range(limit):
		Inputs.append(list(map(float, txta[i].replace(' ','').replace('\n','').split(','))))
		Targets.append(list(map(float, txtb[i].replace(' ','').replace('\n','').split(','))))
	Inputs = tf.convert_to_tensor(Inputs, dtype=tf.float32)
	Targets = tf.convert_to_tensor(Targets, dtype=tf.float32)
	print(Inputs.shape)
	print(Targets.shape)
				
#### IA MODEL ####
model = tf.keras.models.Sequential()
# Add the layers
for i in range(NbLayerHidden):
	if L2Regularization:
		model.add(tf.keras.layers.Dense(NbCellLayer, kernel_regularizer=tf.keras.regularizers.l2(L2RegularizationValue), activation=ActivationType))
	else:
		model.add(tf.keras.layers.Dense(NbCellLayer, activation=ActivationType))
	if LayerDropout:
		model.add(tf.keras.layers.Dropout(LayerDropoutValue))
layer=model.add(tf.keras.layers.Dense(4*3)) # output layer containing 12 cells (4 corner * 3 coords)

model_output = model.predict(Inputs[0:1]) # test current model

# Define custom loss to obtain sum of Relative error
def custom_loss(layer):

	def loss(y_true,y_pred):
		nonnul=tf.fill(tf.shape(y_true), 1e-3)
		test=K.sum(K.abs(y_pred - y_true)/K.maximum(K.abs(y_true),nonnul))
		return test
   
	# Return a function
	return loss

def loss2(y_true,y_pred):
	nonnul=tf.fill(tf.shape(y_true), 1e-3)
	test=K.sum(K.abs(y_pred - y_true)/K.maximum(K.abs(y_true),nonnul))
	return test
	
# Compile the model
model.compile(optimizer=Optimizer,
			loss=custom_loss(layer), # Call the loss function with the selected layer
			#loss=tf.keras.losses.BinaryCrossentropy(reduction=tf.keras.losses.Reduction.SUM,from_logits=True),
			#loss=tf.keras.losses.MeanAbsolutePercentageError(),
			#metrics=['loss']
			)
model.summary()

if restart and os.path.exists('model_simple.h5'):
	import json
	model.load_weights("model_simple.h5")
	
if optimization:

	history = model.fit(
		Inputs, 
		Targets, 
		epochs=NbEpochs, 
		batch_size=BATCH_SIZE,
		validation_split=0.1)

	loss_curve = history.history["loss"]
	loss_val_curve = history.history["val_loss"]

	if True: #to create plot curve (saved as picture)
		plt.plot(loss_curve, label="Train")
		plt.plot(loss_val_curve, label="Val")
		plt.legend(loc='upper left')
		plt.title("Loss")
		if False: #to plot on screen the curve
			plt.show()
		Name='Curve'
		Name+='_NBEPOCHS'+str(NbEpochs)
		Name+='_NBDalleVoisineMAX'+str(NbDalleVoisineMax)
		Name+='_NORMALINDICATOR'+str(NormalIndicator)
		Name+='_NBLAYER'+str(NbLayerHidden)
		Name+='_NBCELLBYLAYER'+str(NbCellLayer)
		Name+='_ACTIVATIONTYPE'+str(ActivationType)
		Name+='_BATCHSIZE'+str(BATCH_SIZE)
		Name+='_L2REGULARIZATION'+str(L2Regularization)
		Name+='_LAYERDROPOUT'+str(LayerDropout)
		Name+='_OPTIMIZER'+str(Optimizer)
		Name+='.png'
		plt.savefig(Name)

	if True:
		import json
		model.save("model_simple.h5")

# TEST PREDICTION MODEL SUR UN CAS AU HASARD
index=random.randint(0,tf.shape(Inputs)[0]-1)
print('random index ->',index)
model_output = model.predict(Inputs[index:index+1])
print('vrai reponse  -> ',Targets[index:index+1])
print('reponse model -> ',model_output)
print('Loss          -> ',loss2(Targets[index:index+1],model_output))
entree=Inputs[index:index+1]
entree=entree.numpy()
vrai=Targets[index:index+1]
vrai=vrai.numpy()
modelresult=model_output
for i in range(len(vrai[0])):
	print('\t Coord ',i+1,'/12 => ',entree[0][i])
	print('\t\t Vrai Reponse -> ',vrai[0][i])
	print('\t\t Prediction   -> ',modelresult[0][i])
	print('\t\t Erreur sur sortie -> ',round(100.*(vrai[0][i]-modelresult[0][i])/vrai[0][i],1),' %')
	Delta_ER=(entree[0][i]-vrai[0][i])
	Delta_EP=(entree[0][i]-modelresult[0][i])
	Delta=round(100.*(Delta_ER-Delta_EP)/Delta_ER,1)
	if np.sign(Delta_ER)==np.sign(Delta_ER):
		CorrectDirection=True
	if abs(Delta)<10:
		print('\t :) :) perfect ! Delta=',Delta,'% less than 10% error!')
	elif abs(Delta)<50.:
		if CorrectDirection:
			print('\t :) Delta=',Delta,'% In good direction and not so far from true!')
		else:
			print('\t :( Delta=',Delta,'% not so far from true response but in bad direction!')
	elif abs(Delta>200.):
		if CorrectDirection:
			print('\t :( Delta=',Delta,'% In good direction but very far from true!')
		else:
			print('\t :( :( :( Delta=',Delta,'% Very far from true response but in bad direction!')
	elif abs(Delta>100.):
		if CorrectDirection:
			print('\t :| Delta=',Delta,'% In good direction but a little far from true!')
		else:
			print('\t :( :( Delta=',Delta,'% not so far from true response but in bad direction!')
#
