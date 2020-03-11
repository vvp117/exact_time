#!/bin/bash


echo "Creating the credentials..."

kubectl apply -f ./secret.yml


echo "Creating the quart deployment and service..."

kubectl create -f ./app-deployment.yml
kubectl create -f ./app-service.yml


echo "Adding the ingress..."

minikube addons enable ingress
kubectl apply -f ./minikube-ingress.yml
