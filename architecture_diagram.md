# Architecture Diagram - Serverless SMS AI Assistant

```
┌─────────────┐    SMS/MMS     ┌─────────────┐    HTTP POST    ┌─────────────┐
│    User     │ ──────────────▶│   Twilio    │ ──────────────▶ │ API Gateway │
│   Phone     │                │  Webhook    │                 │             │
└─────────────┘                └─────────────┘                 └─────────────┘
                                                                        │
                                                                        ▼
                                                                ┌─────────────┐
                                                                │   Lambda    │
                                                                │  Function   │
                                                                │   (main.py) │
                                                                └─────────────┘
                                                                        │
                                    ┌───────────────────────────────────┼───────────────────────────────────┐
                                    │                                   │                                   │
                                    ▼                                   ▼                                   ▼
                            ┌─────────────┐                     ┌─────────────┐                   ┌─────────────┐
                            │   Amazon    │                     │   Amazon    │                   │  DynamoDB   │
                            │  Bedrock    │                     │ Rekognition │                   │   Table     │
                            │ (Claude 3)  │                     │   (Image    │                   │ (Todo List) │
                            │             │                     │  Analysis)  │                   │             │
                            └─────────────┘                     └─────────────┘                   └─────────────┘
                                    │                                   │                                   │
                                    └───────────────────────────────────┼───────────────────────────────────┘
                                                                        │
                                                                        ▼
                                                                ┌─────────────┐
                                                                │  TwiML      │
                                                                │ Response    │
                                                                └─────────────┘
                                                                        │
                                                                        ▼
                                                                ┌─────────────┐
                                                                │   Twilio    │
                                                                │ SMS Reply   │
                                                                └─────────────┘
                                                                        │
                                                                        ▼
                                                                ┌─────────────┐
                                                                │    User     │
                                                                │   Phone     │
                                                                └─────────────┘
```

## Flow Description

1. **User** sends SMS/MMS to Twilio phone number
2. **Twilio** forwards message via HTTP POST webhook to API Gateway
3. **API Gateway** triggers Lambda function
4. **Lambda Function** processes request and routes to appropriate service:
   - **Amazon Bedrock** for Q&A using Claude 3 Sonnet
   - **Amazon Rekognition** for image analysis
   - **DynamoDB** for todo list CRUD operations
5. **Lambda** formats TwiML response
6. **Twilio** receives response and sends SMS reply to user

## Key Components

- **Serverless**: No servers to manage
- **Event-driven**: Triggered by incoming messages
- **Multi-modal**: Handles text and images
- **Persistent**: User data stored in DynamoDB
- **AI-powered**: Uses AWS AI/ML services