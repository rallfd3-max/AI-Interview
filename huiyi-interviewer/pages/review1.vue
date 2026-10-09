<template>
	<view class="container">
		<view class="header">
			<text class="title">AI面试官复试系统</text>
			<text class="subtitle">上海第二工业大学 - 智能面试平台</text>
			<button v-if="ShowExitbutton" class="exit-btn" @click="exitInterview">退出复试</button>
		</view>

		<view class="interview-info">
			<view class="info-grid">
				<view class="info-item">
					<text class="info-label">面试者姓名</text>
					<text class="info-value">{{ interviewInfo.candidateName }}</text>
				</view>
				<view class="info-item">
					<text class="info-label">应聘岗位</text>
					<text class="info-value">{{ interviewInfo.jobTitle }}</text>
				</view>
				<view class="info-item">
					<text class="info-label">面试轮次</text>
					<text class="info-value">复试</text>
				</view>
				<view class="info-item">
					<text class="info-label">面试状态</text>
					<text class="info-value">{{ interviewStatus }}</text>
				</view>
			</view>
		</view>

		<view class="chat-container">
			<view class="chat-header">
				<text class="chat-title">AI面试对话</text>
				<view class="status-indicator">
					<view class="status-dot" :class="{ active: isConnected }"></view><!-- //:class动态绑定样式 -->
					<text class="status-text">{{ isConnected ? '在线' : '离线' }}</text>
				</view>
			</view>

			<scroll-view class="chat-messages" scroll-y="true" :scroll-into-view="lastMsgId" scroll-with-animation
				:scroll-top="scrollTop"><!-- :scroll-top="scrollTop"备用的手动滚动 -->
				<view v-for="(message, index) in messages" :key="message.id" :class="['message', message.sender]"
					:id="'msg' + index">
					<view class="avatar">{{ message.sender === 'user' ? '我' : 'AI' }}</view>
					<view class="text">
						<template v-if="message.typing">
							<view class="typing-indicator">
								<view class="typing-dot"></view>
								<view class="typing-dot"></view>
								<view class="typing-dot"></view>
							</view>
						</template>
						<template v-else>
							<text v-html="message.content"></text>
						</template>
					</view>
				</view>
			</scroll-view>

			<view class="chat-input">
				<textarea ref="chatTextarea" v-model="userInput" placeholder="请输入您的回答..." :focus="autoFocus"
					@confirm="sendMessage" :disabled="isWaitingResponse || ShowExitbutton" @input="adjustTextareaHeight"
					:style="{height: textareaHeight + 'px'}" class="input-textarea"></textarea>
				<button class="voice-btn" @touchstart="startVoiceInput" @touchend="stopVoiceInput"
					:disabled="isRecording">
					<text v-if="!isRecording">🎤 </text>
					<text v-else>🔴 </text>
				</button>
				<button class="send-btn" @click="sendMessage"
					:disabled="isWaitingResponse || !userInput.trim()">发送</button>
			</view>
		</view>

		<view class="session-info">
			<text>会话ID: {{ interviewInfo.mobile }} | 消息Token计数: {{ tokenCounter }}</text>
		</view>
	</view>
</template>


<script>
	export default {
		data() {
			return {
				question: '您好！我是上海第二工业大学的AI面试官，负责今天的复试环节。请确保您处于安静的环境，准备好后点击下方输入框开始面试。',
				isRecording: false,
				textareaHeight: 40,
				recorderManager: uni.getRecorderManager(),
				recordStartTime: 0,
				// speechRecognitionText: "",
				API_BASE_URL: 'http://192.168.10.164:8000',
				interviewInfo: {
					candidateName: '',
					jobTitle: '',
					mobile: '',
					candidateId: '',
					jobId: ''
				},
				isConnected: false,
				tokenCounter: 0,
				isWaitingResponse: false,
				userInput: '',
				autoFocus: false,
				scrollTop: 0,
				lastMsgId: '',
				ShowExitbutton: false,
				EndSuccessfully: false,
				Storagekey1: '',
				Storagekey2: '',
				messages: [{
					id: Date.now(),
					sender: 'bot',
					content: '您好！我是上海第二工业大学的AI面试官，负责今天的复试环节。<br>请确保您处于安静的环境，准备好后点击下方输入框开始面试。',
					typing: false
				}],
				timerIds: [],
			};
		},
		computed: {
			interviewStatus() {
				return this.isConnected ? '面试进行中' : '面试未开始';
			}
		},
		onHide() {
			this.saveConversation();
		},
		onLoad(options) {
			// console.log("从me传递的参数",options);
			this.initRecorder();
			if (options.candidateName && options.jobTitle && options.mobile) {
				this.interviewInfo = {
					candidateName: decodeURIComponent(options.candidateName),
					jobTitle: decodeURIComponent(options.jobTitle),
					mobile: options.mobile,
					candidateId: options.candidateId,
					jobId: options.jobId
				};
			}
			this.Storagekey1 = `interview_conversation_${this.interviewInfo.mobile}`;
			// this.Storagekey2 = `interview_conversation_${this.interviewInfo.candidateId}`;
			// this.candidateid = this.interviewInfo.candidateId;

			this.restoreConversation();

			this.$nextTick(() => {
				this.autoFocus = true;

			});
		},
		methods: {
			saveConversation() {
				const conversationdata = {
					messages: this.messages,
					question: this.question,
					token: this.tokenCounter,
					// interviewInfo: this.interviewInfo,

				};

				const interviewInfo = this.interviewInfo;
				// console.log("存储到本地的conversationdata.messages", conversationdata.messages);
				// console.log("interviewinfo", interviewInfo);

				uni.setStorageSync(this.Storagekey1, JSON.stringify(conversationdata));
				// uni.setStorageSync(this.Storagekey2, JSON.stringify(interviewInfo));

			},

			restoreConversation() {
				const savedData = uni.getStorageSync(this.Storagekey1);
				// const savedInfo = uni.getStorageSync(this.Storagekey2);
				// if (savedData && savedInfo) {
				// console.log("从本地取的savedData", savedData);

				if (savedData) {
					try {
						const conversationData = JSON.parse(savedData);
						this.messages = conversationData.messages || [];
						this.question = conversationData.question || '';
						this.tokenCounter = conversationData.tokenCounter || 0;
						// console.log("从本地取的conversationData.messages", conversationData.messages);


						// const interviewInfo = JSON.parse(savedInfo);
						// this.interviewInfo.candidateName = interviewInfo.candidateName;
						// this.interviewInfo.candidateId = interviewInfo.candidateId;
						// this.interviewInfo.jobTitle = interviewInfo.jobTitle;
						// this.interviewInfo.mobile = interviewInfo.mobile;
						// this.interviewInfo.jobId = interviewInfo.jobId;
						// console.log("存储的信息", savedInfo);
						// console.log("现在的信息", this.interviewInfo);

						this.$nextTick(() => {
							this.forceScrollBottom();
						});

					} catch (e) {
						console.log('恢复对话记忆失败', e);
					}
				}
			},

			clearConversationStorage() {
				uni.clearStorageSync(this.Storagekey1);
				console.log("上一次的对话信息已删除");
			},

			adjustTextareaHeight(e) {
				const lineHeight = 22;
				const minHeight = 40;
				const maxHeight = 120;
				const lines = this.userInput.split('\n').length;
				const newHeight = Math.min(Math.max(lines * lineHeight, minHeight), maxHeight);
				this.textareaHeight = newHeight;
			},

			async exitInterview() {
				this.EndSuccessfully = true;
				uni.showModal({
					title: '确认退出',
					content: '您确定要结束本次复试吗？',
					success: async (res) => {
						if (res.confirm) {
							try {
								uni.showLoading({ //跳转等待需调用hideloading
									title: '正在退出...'
								});
								// console.log('提交字段:', {
								//   mobile: this.interviewInfo.mobile,
								//   candidateName: this.interviewInfo.candidateName
								// });
								const [error, response] = await new Promise(resolve => {
									uni.request({
										url: `${this.API_BASE_URL}/exit`,
										header: {
											'Content-Type': 'application/x-www-form-urlencoded' // 不指定 JSON 格式
										},
										method: 'POST', //提交数据，不被缓存，安全性高一些
										data: {
											mobile: this.interviewInfo.mobile,
											candidateName: this.interviewInfo
												.candidateName,
											candidateId: this.interviewInfo
												.candidateId,
											jobId: this.interviewInfo.jobId,
											jobTitle: this.interviewInfo
												.jobTitle
										},
										success: (res) => resolve([null, res]),
										fail: (err) => resolve([err, null])
									});
								});

								if (error) throw error;
								// uni.showToast({//自动消失的短提示
								// 	title: '已成功退出复试',
								// 	icon: 'success'
								// });
								// setTimeout(() => {
								// 	uni.redirectTo({//不会保存当前页
								// 		url: '/pages/jobselect?result=exit'
								// 	});
								// }, 1500);
								uni.showToast({
									title: '退出成功',
									icon: 'success',
									duration: 1500, // Toast 显示 1.5 秒
									complete: () => { // Toast 消失后跳转
										uni.redirectTo({
											url: `/pages/jobselect?result=exit&mobile=${this.interviewInfo.mobile}&candidateId=${this.interviewInfo.candidateId}&candidateName=${this.interviewInfo.candidateName}&jobTitle=${this.interviewInfo.jobTitle}&jobId=${this.interviewInfo.jobId}`
										});
									}
								});
								this.clearConversationStorage();
							} catch (error) {
								console.error('退出失败:', error);
								uni.showToast({
									title: '退出失败: ' + (error.message || '网络错误'),
									icon: 'none'
								});
							} finally {
								uni.hideLoading();
							}
						}
					}
				});
			},
			async exitInterviewpassively() {
				const [error, response] = await new Promise(resolve => {
					uni.request({
						url: `${this.API_BASE_URL}/exit`,
						header: {
							'Content-Type': 'application/x-www-form-urlencoded' // 不指定 JSON 格式
						},
						method: 'POST', //提交数据，不被缓存，安全性高一些
						data: {
							mobile: this.interviewInfo.mobile,
							candidateName: this.interviewInfo.candidateName
						},
						success: (res) => resolve([null, res]),
						fail: (err) => resolve([err, null])
					});
				});
				if (error) throw error;
				console.log("End passively")
				this.clearConversationStorage();
			},

			initRecorder() {
				let self = this;
				this.recorderManager.onStart(() => {
					console.log('录音开始');
					self.isRecording = true;
				});
				//监听录音状态
				this.recorderManager.onStop((res) => {
					console.log('录音结束', res.tempFilePath);
					self.isRecording = false;
					const recordEndTime = new Date().getTime();
					const timeDiffSeconds = Math.round((recordEndTime - self.recordStartTime) /
						1000);

					if (timeDiffSeconds < 1) {
						uni.showToast({
							icon: "none",
							title: "说话时间太短..."
						});
						return;
					}
					self.uploadVoiceFile(res.tempFilePath);
				});
			},
			uploadVoiceFile(filePath) {
							let self = this;
							uni.uploadFile({
								url: `http://192.168.98.3:8001/recognize`,
								filePath: filePath,
								name: 'audio',
								formData: {
									query: filePath,
								},
								header: {
									'Content-Type': 'multipart/form-data'
								},
								success: (uploadRes) => {
									console.log(uploadRes);
									if (uploadRes.statusCode === 200) {
										const resData = JSON.parse(uploadRes.data);
										console.log(resData);
										if (resData.status === 200) {
											self.userInput += resData.text || '';
											
											self.autoFocus = true;
										} else {
											uni.showToast({
												title: '语音识别失败: ' + resData.msg,
												icon: 'none'
											});
										}
									}
								},
					fail: (err) => {
						console.error('上传失败', err);
						uni.showToast({
							title: '上传失败',
							icon: 'none'
						});
					}
				});
			},
			


			startVoiceInput() {
				this.recordStartTime = new Date().getTime();
				this.recorderManager.start({
					format: 'mp3',
					sampleRate: 16000,
					numberOfChannels: 1,
					encodeBitRate: 192000,
				});
			},

			stopVoiceInput() {
				this.recorderManager.stop();
			},

			forceScrollBottom(index = null) {
				this.$nextTick(() => {
					if (index !== null) {
						this.lastMsgId = 'msg' + index; //指定位置
					} else {
						this.lastMsgId = 'msg' + (this.messages.length - 1); //最后一位
					}
				});
			},

			addMessage(content, isUser = false, typing = false) {
				const message = {
					id: Date.now() + Math.random(),
					sender: isUser ? 'user' : 'bot',
					content: content,
					typing: typing
				};
				this.messages.push(message);
				this.tokenCounter += content.length;
				this.forceScrollBottom(); //跳转到最后
				this.saveConversation();
			},


			async sendMessage() {
				if (this.isWaitingResponse || !this.userInput.trim()) return;

				const message = this.userInput.trim(); //strip() trimStart trimEnd
				this.addMessage(message, true);
				this.userInput = '';
				this.isWaitingResponse = true;
				this.isConnected = true;

				// 添加打字效果消息
				this.addMessage('', false, true);
				const typingMsgIndex = this.messages.length - 1;

				try {
					const url =
						`${this.API_BASE_URL}/chat?query=${encodeURIComponent(message)}&context=${this.interviewInfo.mobile}&question=${this.question}`;
					// console.log("发送信息时传递的参数", message, this.interviewInfo.mobile, this.question);
					const [error, response] = await new Promise(resolve => {
						uni.request({
							url: url,
							method: 'GET', //查询数据
							success: (res) => resolve([null, res]), //初始化
							fail: (err) => resolve([err, null])
						});
					});

					if (error) throw error;

					const responseData = response.data || '';

					let responseContent = '';

					if (typeof responseData === 'string') {
						const lines = responseData.split('\n');
						for (const line of lines) {
							if (line.startsWith('data:')) {
								const content = line.substring(5).trim();
								let cleanContent = content;
								if (cleanContent.startsWith('"') && cleanContent.endsWith('"')) {
									cleanContent = cleanContent.substring(1, cleanContent.length -
										1);
									// console.log("原始响应:", cleanContent);
								}
								responseContent += cleanContent;
								this.question = responseContent;
								// console.log("question",this.question)
							}
						}

					} else if (typeof responseData === 'object') {
						// 如果是JSON响应，提取可能的message字段
						responseContent = responseData.message || JSON.stringify(responseData);
					}
					if (this.question.endsWith("^^")) {
						this.ShowExitbutton = true;

					}
					// console.log("exitbutton",this.ShowExitbutton)
					responseContent = responseContent.match(/当前询问内容:(.*?)计划之后询问:/);
					responseContent = responseContent[1]
					responseContent = responseContent.replace(/\\n/g, '').replace(/\n/g, '');
					// console.log("从后端发来的responseData", responseData);
					// 移除打字效果消息
					this.messages.splice(typingMsgIndex, 1);

					// 添加空消息用于逐字显示
					this.addMessage('', false, false);
					const aiMsgIndex = this.messages.length - 1;

					// 逐字显示效果
					// let index = 0;
					// const typeWriter = () => {
					// 	if (index < responseContent.length) {
					// 		this.messages[aiMsgIndex].content += responseContent.charAt(index);
					// 		index++;
					// 		this.forceScrollBottom(aiMsgIndex); //跟踪滚动
					// 		this.timerIds.push(setTimeout(typeWriter, 50)); // 控制打字速度
					// 	}
					// };
					// typeWriter();
					const typeWriter = () => {
						return new Promise(resolve => {
							let index = 0;
							const type = () => {
								if (index < responseContent.length) {
									this.messages[aiMsgIndex].content += responseContent.charAt(index);
									index++;
									this.forceScrollBottom(aiMsgIndex);
									this.timerIds.push(setTimeout(type, 50));
								} else {
									resolve();
								}
							};
							type();
						});
					};

					await typeWriter(); // 等待打字完成
					this.saveConversation(); // 然后保存


				} catch (error) {
					console.error('发送消息出错:', error);
					this.messages.splice(typingMsgIndex, 1); //删除"正在输入"
					this.addMessage('抱歉，发送消息时出现错误', false);
				} finally {
					this.isWaitingResponse = false;
				}
			}
		},
		beforeDestroy() {
			this.timerIds.forEach(id => clearTimeout(id));
			if (this.EndSuccessfully == false && this.ShowExitbutton == true) {
				this.exitInterviewpassively()
				// this.exitInterview()
			}

		}
	}
</script>


<style>
	@import url("review.css");
</style>