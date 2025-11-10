[**English**](./README.md)

# ComfyUI-Jumper
複数のComfyUIをリモート接続してStringとImagesを渡す事ができます。<br />
ローカルやクラウドGPU（Ranpod、Vast.aiなど）のComfyUIと接続できます。<br />
[YouTube動画デモ](https://youtu.be/VYwOMiZOJfU)<br />

*リモート側*
![example](https://github.com/myonmu0/ComfyUI-Jumper/blob/main/examples/remote.png)
*ローカル側*
![example](https://github.com/myonmu0/ComfyUI-Jumper/blob/main/examples/local.png)


## メリット
- **リソースの統合：** 複数のコンピューターを使って１つの作業を行えます。

- **利便性：** ローカルのComfyUI内で、リモートComfyUIを操作して生成データを受け取れるのは状況次第では便利です。

- **プライバシー：** リモート側でサンプル画像のようなワークフローを実行すると、入力・生成データがディスクに書き込まれない為、あなたのデータが漏洩または見られる可能性が下がると思います。プライバシーを期待する場合はリモート側で入力・生成データをPreview/Save系のノードに繋げないで下さい。


## Install
```
cd ComfyUI/custom_nodes/
git clone https://github.com/myonmu0/ComfyUI-Jumper
```

## チュートリアル
1. クラウドGPUでサーバーをレンタルするか、ローカルで２つComfyUIを起動します。<br />

2. ポート開放、通信は必ずSSHトンネルなどのセキュアな方法で行いましょう。
```
ssh root@REMOTE_IP -p REMOTE_PORT -NL 8282:localhost:8282
```
 - *デフォルトポートは8282ですが、nodes.pyのDEFAULT_ADDRを編集又はノードで変更できます。*
 - *ローカルとローカルを接続する場合、このステップは必要ありません。*<br />

3. ローカルとリモートでComfyUIを起動します。サンプルのワークフローを読み込みましょう、examples/local.jsonをローカル、examples/remote.jsonをリモート側で読み込んで実行して動作を確認してみましょう。
 - *ブラウザでリモートComfyUIにアクセスする際にも、セキュリティ、シンプル、汎用性の観点からSSHトンネルはおすすめです。更にシークレットモード/プライベートモードでアクセスすると、０ブラウザデータで開始して、０ブラウザデータで終わるためクリーンでおすすめです。*

⚠️ **既知の問題:**
このノードが実行されてる時は、ジョブキャンセルボタンが効かないのでComfyUIを再起動して下さい。


## 詳細 
ノードの"mode"はローカル側では"Client"、リモート側では"Server"を設定しましょう。

１つのワークフローには、１つのJumperノードの連結（チェーン）が基本です。

ノードの"order"は送信/受信の順番を決定する重要なものです、正しく連結させましょう。
サンプルのワークフローの様にJumper末尾ノードの"order"をPreview Anyノードに繋ぐなどして、最低１つは最後に繋がってる状態にして下さい。

| send_as | Size        | CPU         | About                                    |
| --------- | -------------  | --------------- | ------------------------------------------------- |
| png     | Small       |  Moderate   | Convert tensor to png before sending.	<sub>Progress bar: 1 = Conversion, 2 = Sending</sub>    |
| zlib    | Large       |  Moderate   | Compress tensor before sending.          |
| raw     | Very Large  |  Very Low   | Raw tensor are send.  | 





