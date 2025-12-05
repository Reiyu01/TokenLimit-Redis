#介紹

測試Redis進行Gateway測試Token扣款管理


User --->  進入到Redis ----->Redis判斷是否有使用者資料，若沒有則呼叫資料庫撈取，並設定憑證為1小時候過期

Redis 得到使用者資料後，會在記憶體內運算加總，並背後透過非同步方式寫入到db當中

優點:這一小時內，使用者每次呼叫的計算方式都在redis內的暫存資料，並非同步更新至db當中
若1小時一到，Redis則從db當中撈取資料。能確保資料皆為最新。

缺點:
可能db方面需要有方法來應付高併發高流量。可能需要MQ等之類的方式寫入
redis皆為暫存資料，若因此斷電則該一小時內的資料皆消失，可能需要設定Redis非暫存而實際保留。

#檔案介紹

init_db.py:初始化db資料庫，執行後會創建名為token_manager.db資料庫並模擬一個用戶:sk-test餘額為10000

main.py:redis與db流程，參照#介紹

test_client.py:模擬sk-test用戶呼叫


#啟動方式

uvicorn main:app --reload

另一個終端機:
python test_client.py  