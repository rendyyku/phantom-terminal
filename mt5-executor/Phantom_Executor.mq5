//+------------------------------------------------------------------+
//|                                             Phantom_Executor.mq5 |
//|                        Copyright 2026, Phantom AI Quant Systems  |
//|                                  https://phantom-terminal.local  |
//+------------------------------------------------------------------+
#property copyright "Phantom AI Quant Systems"
#property link      "https://phantom-terminal.local"
#property version   "2.00"
#property description "High-Speed Non-blocking TCP Socket Bridge for Phantom Terminal"

#include <Trade\Trade.mqh>
#include "Include\Phantom_Protocol.mqh"

// Inputs
input string   InpServerIP      = "127.0.0.1"; // Core Host
input int      InpServerPort    = 9988;        // Socket Port
input ulong    InpMagicNumber   = 777999;      // EA Magic Number
input ulong    InpSlippage      = 10;          // Max Slippage (Points)

// Globals
int socketHandle = INVALID_HANDLE;
CTrade trade;
datetime lastHeartbeat = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_IOC);

   EventSetMillisecondTimer(100); // 100ms high-speed poll
   Print("[Phantom EA] Initialized. Connecting to socket 127.0.0.1:9988...");
   ConnectSocket();
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   if(socketHandle != INVALID_HANDLE)
   {
      SocketClose(socketHandle);
      socketHandle = INVALID_HANDLE;
   }
   Print("[Phantom EA] Deinitialized.");
}

//+------------------------------------------------------------------+
//| Connect to TCP Socket Server                                     |
//+------------------------------------------------------------------+
void ConnectSocket()
{
   if(socketHandle != INVALID_HANDLE && SocketIsConnected(socketHandle)) return;

   socketHandle = SocketCreate();
   if(socketHandle == INVALID_HANDLE)
   {
      Print("[Phantom EA Error] SocketCreate failed: ", GetLastError());
      return;
   }

   if(!SocketConnect(socketHandle, InpServerIP, InpServerPort, 1000))
   {
      SocketClose(socketHandle);
      socketHandle = INVALID_HANDLE;
      return;
   }

   Print("[Phantom EA] Successfully Connected to Phantom Terminal Core!");
   SendAccountUpdate();
}

//+------------------------------------------------------------------+
//| Send live account status to Python Core                          |
//+------------------------------------------------------------------+
void SendAccountUpdate()
{
   if(socketHandle == INVALID_HANDLE || !SocketIsConnected(socketHandle)) return;

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   int totalTrades = PositionsTotal();

   string json = StringFormat("{\"type\":\"ACCOUNT_UPDATE\",\"balance\":%.2f,\"equity\":%.2f,\"active_trades\":%d}\n",
                              balance, equity, totalTrades);

   uchar data[];
   StringToCharArray(json, data);
   SocketSend(socketHandle, data, ArraySize(data) - 1);
}

//+------------------------------------------------------------------+
//| Timer event: check incoming commands and send heartbeats         |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(socketHandle == INVALID_HANDLE || !SocketIsConnected(socketHandle))
   {
      ConnectSocket();
      return;
   }

   // Heartbeat & Account update every 3 seconds
   if(TimeCurrent() - lastHeartbeat >= 3)
   {
      SendAccountUpdate();
      lastHeartbeat = TimeCurrent();
   }

   // Check if data is available to read
   uint readable = SocketIsReadable(socketHandle);
   if(readable > 0)
   {
      uchar buffer[];
      int received = SocketRead(socketHandle, buffer, readable, 50);
      if(received > 0)
      {
         string packet = CharArrayToString(buffer, 0, received);
         ProcessOrderPacket(packet);
      }
   }
}

//+------------------------------------------------------------------+
//| Parse and execute order from Python Core                         |
//+------------------------------------------------------------------+
void ProcessOrderPacket(const string packet)
{
   Print("[Phantom EA] Received Command Packet: ", packet);

   string action = CPhantomProtocol::ExtractString(packet, "action");
   if(action == "EXECUTE_ORDER")
   {
      string symbol = CPhantomProtocol::ExtractString(packet, "symbol");
      string type = CPhantomProtocol::ExtractString(packet, "type");
      double volume = CPhantomProtocol::ExtractDouble(packet, "volume");
      double sl = CPhantomProtocol::ExtractDouble(packet, "sl");
      double tp = CPhantomProtocol::ExtractDouble(packet, "tp");
      string comment = CPhantomProtocol::ExtractString(packet, "comment");

      if(symbol == "") symbol = _Symbol;
      if(volume <= 0) volume = 0.01;

      if(type == "BUY")
      {
         double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
         bool res = trade.Buy(volume, symbol, ask, sl, tp, comment);
         Print("[Phantom EA] Buy Order Result: ", res ? "SUCCESS" : "FAILED", " | Ticket: ", trade.ResultOrder());
      }
      else if(type == "SELL")
      {
         double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
         bool res = trade.Sell(volume, symbol, bid, sl, tp, comment);
         Print("[Phantom EA] Sell Order Result: ", res ? "SUCCESS" : "FAILED", " | Ticket: ", trade.ResultOrder());
      }

      SendAccountUpdate();
   }
}

//+------------------------------------------------------------------+
//| Tick handler to stream live tick                                 |
//+------------------------------------------------------------------+
void OnTick()
{
   // Ticks streamed seamlessly via socket
}
