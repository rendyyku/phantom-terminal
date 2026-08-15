//+------------------------------------------------------------------+
//|                                              Phantom_Protocol.mqh|
//|                        Copyright 2026, Phantom AI Quant Systems  |
//|                                  https://phantom-terminal.local  |
//+------------------------------------------------------------------+
#property copyright "Phantom AI Quant Systems"
#property link      "https://phantom-terminal.local"
#property strict

//+------------------------------------------------------------------+
//| Simple and Fast JSON Key-Value Extraction for MQL5               |
//+------------------------------------------------------------------+
class CPhantomProtocol
{
public:
   static string ExtractString(const string json, const string key)
   {
      string search = "\"" + key + "\":\"";
      int start = StringFind(json, search);
      if(start == -1) return "";
      start += StringLen(search);
      int end = StringFind(json, "\"", start);
      if(end == -1) return "";
      return StringSubstr(json, start, end - start);
   }

   static double ExtractDouble(const string json, const string key)
   {
      string search = "\"" + key + "\":";
      int start = StringFind(json, search);
      if(start == -1) return 0.0;
      start += StringLen(search);
      
      int end1 = StringFind(json, ",", start);
      int end2 = StringFind(json, "}", start);
      int end = -1;
      
      if(end1 != -1 && end2 != -1) end = MathMin(end1, end2);
      else if(end1 != -1) end = end1;
      else end = end2;
      
      if(end == -1) return 0.0;
      string valStr = StringSubstr(json, start, end - start);
      StringTrimLeft(valStr);
      StringTrimRight(valStr);
      return StringToDouble(valStr);
   }

   static long ExtractLong(const string json, const string key)
   {
      return (long)ExtractDouble(json, key);
   }
};
