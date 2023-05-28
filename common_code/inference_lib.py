import boto3
import time
import json

    
def descirbe_endpoint(endpoint_name):
    '''
    엔드폰인트 생성 유무를 확인. 생성 중이면 기다림.
    '''
    sm_client = boto3.client("sagemaker")

    while(True):
        response = sm_client.describe_endpoint(
            EndpointName= endpoint_name
        )    
        status = response['EndpointStatus']
        if status == 'Creating':
            print("Endpoint is ", status)
            time.sleep(60)
        else:
            print("Endpoint is ", status)
            break


def invoke_inference(endpoint_name, prompt):
    '''
    KoAlpaca 프롬프트를 제공하여 엔드포인트 호출
    '''
    client = boto3.client("sagemaker-runtime")
    
    content_type = "text/plain"
    response = client.invoke_endpoint(
        EndpointName=endpoint_name, ContentType=content_type, Body=prompt
    )
    #print(response["Body"].read())
    res = response["Body"].read().decode()
    print (eval(res)[0]['generated_text'])

            
        
def query_endpoint_with_text_payload(plain_text, endpoint_name, content_type="text/plain"):
    '''
    content_type 이 text/plain 인 경우 사용
    '''
    client = boto3.client("runtime.sagemaker")
    response = client.invoke_endpoint(
        EndpointName=endpoint_name, ContentType=content_type, Body=plain_text
    )
    return response


def parse_response_text_model(query_response):
    '''
    content_type 이 text/plain 인 경우 사용
    '''
    
    model_predictions = json.loads(query_response["Body"].read())
    # print("model_predictions: \n", model_predictions)
    generated_text = model_predictions[0]["generated_text"]
    return generated_text

################################################
# Embedding Handler
################################################

from langchain.embeddings.sagemaker_endpoint import EmbeddingsContentHandler
from langchain.embeddings import SagemakerEndpointEmbeddings
from langchain.llms.sagemaker_endpoint import ContentHandlerBase
from typing import Any, Dict, List, Optional

class SagemakerEndpointEmbeddingsJumpStart(SagemakerEndpointEmbeddings):
    def embed_documents(self, texts: List[str], chunk_size: int = 5) -> List[List[float]]:
        """Compute doc embeddings using a SageMaker Inference Endpoint.

        Args:
            texts: The list of texts to embed.
            chunk_size: The chunk size defines how many input texts will
                be grouped together as request. If None, will use the
                chunk size specified by the class.

        Returns:
            List of embeddings, one for each text.
        """
        results = []
        _chunk_size = len(texts) if chunk_size > len(texts) else chunk_size

        print("text size: ", len(texts))
        print("_chunk_size: ", _chunk_size)

        for i in range(0, len(texts), _chunk_size):
            response = self._embedding_func(texts[i : i + _chunk_size])
            print
            results.extend(response)
        return results

import numpy as np
    
class EmbeddingContentHandler(EmbeddingsContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs={}) -> bytes:
        input_str = json.dumps({"inputs": prompt, **model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        print("response_json shape: ", np.array(response_json).shape)
        print("response_json shape: ", np.array(response_json[0][0][0]).shape)        
        # print("response_json in EmbeddingContentHandler \n",  response_json)
        # embeddings = response_json["embedding"][0]
        embeddings = response_json[0][0]     
        return embeddings


################################################
# LLM  Handler
################################################
from langchain.llms.sagemaker_endpoint import LLMContentHandler

class KorLLMContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs={}) -> bytes:
        input_str = json.dumps({"text_inputs": prompt, **model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json["generated_texts"][0]
