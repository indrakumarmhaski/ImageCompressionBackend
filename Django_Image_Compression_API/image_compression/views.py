from django.shortcuts import render
from rest_framework import generics
from .models import CompressedImage
from .serializers import CompressedImageSerializer
from django.http import HttpResponse
from PIL import Image
from io import BytesIO
from django.core.files import File
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.conf import settings
import boto3
from botocore.exceptions import NoCredentialsError
import uuid 

class CompressImageView(generics.CreateAPIView):
    queryset = CompressedImage.objects.all()
    serializer_class = CompressedImageSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        uploaded_image = self.request.data.get('image')
        image = Image.open(uploaded_image)
        
        # Perform image compression here (e.g., resize or reduce quality)
        compressed_image = BytesIO()
        image.save(compressed_image, format='JPEG', quality=10)
        
        # Wrap the compressed image data in a Django File object
        compressed_image_data = File(compressed_image, name='compressed_image.jpg')
        serializer.validated_data['image'] = compressed_image_data

        # Save the compressed image to S3
        try:
            s3 = boto3.client('s3')
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            key = f'media/images/compressed_image_{uuid.uuid4()}.jpg'
            compressed_image.seek(0)
            content_disposition = f'attachment; filename="{key.split("/")[-1]}"'
            s3.upload_fileobj(compressed_image, bucket_name, key, ExtraArgs={'ContentType': 'image/jpeg', 'ContentDisposition': content_disposition,})

            # Save the S3 object URL to the serializer
            serializer.validated_data['image'] = key
            serializer.save()
        except NoCredentialsError:
            # Handle AWS credentials error
            print("Theere is a error")
            pass

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        # Retrieve the compressed image URL from the serializer's save method
        compressed_image_key = response.data.get('image')

        # Build the S3 object URL for the compressed image
        s3_url = compressed_image_key.split("?")[0]
        print(s3_url)

        # Include the S3 object URL in the response
        response_data = {
            'download_url': s3_url,
            'content_disposition': f'attachment; filename="{s3_url.split("/")[-1]}"',
        }

        return Response(response_data)



