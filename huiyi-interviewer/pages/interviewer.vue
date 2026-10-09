<template>
	<view class="bg">
		<video v-if="questionList.length > 0" id="myVideo" class="ai-interviewer-video"
			:src="questionList[currentIndex].aiSrc" controls="false" object-fit="cover" autoplay="true"
			show-center-play-btn="false" show-loading="false" vslide-gesture-in-fullscreen="false"
			enable-progress-gesture="false" enable-play-gesture="false" @ended="onVideoEnded">

			<cover-view class="operator-content">
				<cover-view class="question-wrapper">
					<cover-view class="question-number">第{{currentIndex+1}}题/共{{questionList.length}}题</cover-view>
					<cover-view class="question-content">{{questionList[currentIndex].question}}</cover-view>
				</cover-view>
			</cover-view>

			<cover-view class="bottom-side-box">
				<cover-view class="btn-go-login" @click="startAnswer()" v-if="isRecordAudio == 1 && videoPlayed">
					<cover-view class="login-btn-text">点我答题</cover-view>
				</cover-view>
				<cover-view class="btn-go-login" @click="nextQuestion(currentIndex)" v-if="isRecordAudio == 2">
					<cover-view class="next-btn-text">回答完毕，下一题</cover-view>
				</cover-view>
				<cover-view class="btn-submit" @click="submitInterview(currentIndex)" v-if="isRecordAudio == 3">
					<cover-view class="submit-btn-text">面试结束，点我提交</cover-view>
				</cover-view>
			</cover-view>

			<cover-view class="record-box">
				<cover-view class="tips-text"
					v-if="isRecordAudio == 2">正在录音中...（总耗时:{{formatSeconds(totalTimer)}}）</cover-view>
			</cover-view>

		</video>
	</view>
</template>

<script>
	var app = getApp();
	export default {
		data() {
			// #ifdef APP-PLUS
			const recorderManager = uni.getRecorderManager();
			const innerAudioContext = uni.createInnerAudioContext();
			innerAudioContext.autoplay = true;
			// #endif

			return {
				btnValue: "",
				isRecordAudio: 1,
				
				// #ifdef APP-PLUS
				recorderManager,
				innerAudioContext,
				isSubmitting: false,
				recorderVoice: {
					voicePath: '',
					speakVoiceDuration: 0,
				},
				// #endif
				videoPlayed: false,
				currentIndex: 0,
				questionList: [],
				answerList: [],
				questionList2: [{
						question: "MongoDB是什么？有没有事务类型呢类？",
						aiSrc: "../static/ai/ai-interviewer-003.mp4",
					}, {
						question: "SpringCloud和SpringBoot的区别是什么？",
						aiSrc: "../static/ai/ai-interviewer-003.mp4",
					}
				],
				totalTimer: 1,
				jobName: "",
				jobId: "",
				recordStartTime: null,
				smsTimer: null,
				videoContext: null
			}
		},
		onLoad(options) {
			this.jobName = options.jobName;
			this.jobId = options.jobId;
			console.log("接收到的 jobName:", this.jobName);
			console.log("jobId", this.jobId);
			var me = this;

			// #ifdef APP-PLUS
			this.initRecorder();
			// #endif

			this.initQuestion();
			this.preloadResultPage();
		},
		onUnload() {
			clearInterval(this.smsTimer)
			if (this.recorderManager) {
				this.recorderManager.stop()
			}
			this.stopVideoPlayback()
		
			// 强制清除视频组件
			this.videoContext = null
			// this.questionList = []
		},
		
		onReady: function(res) {
			this.videoContext = uni.createVideoContext('myVideo')
		},
		
		methods: {
			
			
			stopVideoPlayback() {
				if (this.videoContext) {
					this.videoContext.stop();
					this.videoContext.seek(0);
				}
			},
			
			preloadResultPage() {
				const candidateInfo = app.getUserInfoSession();
				if (candidateInfo) {
					const url = `/pages/me?jobId=${candidateInfo.jobId}&candidateId=${candidateInfo.candidateId}`;
					uni.preloadPage({ url });
				}
			},
			
			initQuestion() {
				var me = this;
				var candidateInfo = app.getUserInfoSession();
				console.log(candidateInfo);
				var candidateId = candidateInfo.candidateId;
				var serverUrl = app.globalData.serverUrl;
				console.log(this.jobName);
				uni.request({
					method: "GET",
					url: serverUrl + "/questionLib/prepareQuestion?candidateId=" + candidateId + "&jobName=" + this.jobName,
					success(result) {
						console.log(result);
						var status = result.data.status;
						if (status == 200) {
							var questionList = result.data.data;
							me.questionList = questionList;
							console.log(me.questionList);
						} else {
							uni.showToast({
								title: result.data.msg,
								icon: "none",
								duration: 3000
							});
						}
					}
				});
			},

			initRecorder() {
				let self = this;

				// #ifdef APP-PLUS
				this.recorderManager.onStop(function(res) {
					var recordEndTime = new Date();
					var recordStartTime = self.recordStartTime;
					var timeDiff = recordEndTime.getTime() - recordStartTime.getTime();
					var timeDiffSeconds = Math.round(timeDiff / 1000);

					if (timeDiffSeconds < 1) {
						uni.showToast({
							icon: "none",
							title: "说话时间太短..."
						})
						return;
					}

					var recorderVoice = {
						speakVoiceDuration: timeDiffSeconds,
						voicePath: res.tempFilePath
					};

					var currentIndex = self.currentIndex;
					var questionList = self.questionList;
					
					if (currentIndex < questionList.length - 1) {
						self.currentIndex++;
						self.isRecordAudio = 1;
						clearInterval(self.smsTimer);

						self.$nextTick(() => {
							self.videoContext.play();
						});
					} else {
						self.isRecordAudio = 3;
					}

					// 后台上传音频
					self.uploadVoiceInBackground(res.tempFilePath, currentIndex);
				});
				// #endif

				var innerAudioContext = uni.createInnerAudioContext();
				this.innerAudioContext = innerAudioContext;
				this.innerAudioContext.autoplay = true;

				this.innerAudioContext.onEnded(function(res) {
					self.voicePlayingIndex = -1;
				});
			},

			async uploadVoiceInBackground(voicePath, currentIndex) {
				 const self = this; // 或者使用箭头函数
				try {
					var userId = app.getUserInfoSession().id;
					var serverUrl = app.globalData.serverUrl;
					
					const result = await this.uploadFileAsync({
						url: serverUrl + "/speech/uploadVoice",
						filePath: voicePath,
						name: "file",
						header: {
							headerUserId: userId,
							headerUserToken: app.getUserSessionToken()
						}
					});
					
					if (result.statusCode == 200) {
						var res = JSON.parse(result.data);
						if (res.status == 200) {
							self.questionList[currentIndex].answerContent = res.data;
							console.log("list",self.questionList);
							console.log("音频上传成功:", res.data);
						}
					}
				} catch (error) {
					console.error("音频上传失败:", error);
					self.questionList[currentIndex].answerContent = "";
				}
			},

			uploadFileAsync(options) {
				return new Promise((resolve, reject) => {
					uni.uploadFile({
						...options,
						success: resolve,
						fail: reject
					});
				});
			},

			startRecord() {
				this.recorderManager.start({
					duration: 600000,
					sampleRate: 16000,
					numberOfChannels: 1,
				});
				this.recordStartTime = new Date();
			},
			
			endRecord() {
				this.recorderManager.stop();
			},

			submitInterview() {
				this.stopVideoPlayback();
				
				if (this.isSubmitting || this.isRecordAudio !== this.questionList.length) return;
				this.isSubmitting = true;
				
				// 立即跳转页面
				const candidateInfo = app.getUserInfoSession();
				uni.redirectTo({
					url: `/pages/me?jobId=${candidateInfo.jobId}&candidateId=${candidateInfo.candidateId}&mobile=${candidateInfo.mobile}`,
					animationType: "slide-in-bottom",
				});
				
				// 后台继续处理提交逻辑
				this.continueSubmitInBackground();
			},

			async continueSubmitInBackground() {
				const self = this; // 保存当前 this 指向
				try {
					// 停止录音器
					if (this.recorderManager) {
						await this.stopRecorderAsync();
					}
					
					
					clearInterval(this.smsTimer);
					
					// 准备提交数据
					const candidateInfo = app.getUserInfoSession();
					console.log(self.questionList);
					const bo = {
						candidateId: candidateInfo.candidateId,
						jobId: candidateInfo.jobId,
						questionAnswerList: self.questionList,
						totalSeconds: self.totalTimer,
					};
					console.log(bo);
					// 提交到服务器
					const serverUrl = app.globalData.serverUrl;
					const result = await this.requestAsync({
						method: "POST",
						url: serverUrl + "/interviewRecord/collect",
						data: bo
					});
					
					console.log("后台提交完成", result);
					
				} catch (error) {
					console.error("后台提交失败", error);
					// 可以在这里添加错误日志上报
				} finally {
					this.isSubmitting = false;
				}
			},

			stopRecorderAsync() {
				return new Promise((resolve) => {
					if (!this.recorderManager) {
						resolve();
						return;
					}
					
					const stopTimeout = setTimeout(() => {
						resolve();
					}, 1000);
					
					this.recorderManager.stop();
					this.recorderManager.onStop(() => {
						clearTimeout(stopTimeout);
						resolve();
					});
				});
			},

			requestAsync(options) {
				return new Promise((resolve, reject) => {
					uni.request({
						...options,
						success: resolve,
						fail: reject
					});
				});
			},

			onVideoEnded() {
				this.videoPlayed = true;
			},
			
			
			startAnswer() {
				if (!this.videoPlayed) {
					uni.showToast({
						title: '请先观看完视频',
						icon: 'none',
						duration: 2000
					});
					return;
				}
				this.isRecordAudio = 2;
				this.doTimer();
				this.startRecord();
			},

			nextQuestion(index) {
				this.endRecord();
				this.videoPlayed = false;
				this.isRecordAudio = 1;
			},

			doTimer() {
				var me = this;
				var totalTimer = this.totalTimer;
				var timerFunction = function() {
					me.totalTimer = totalTimer++;
				};
				var smsTimer = setInterval(timerFunction, 1000);
				this.smsTimer = smsTimer;
			},

			formatSeconds(t) {
				let h = parseInt(`${t / 60 / 60}`)
				let m = parseInt(`${t / 60 % 60}`)
				let s = parseInt(`${t % 60}`)
				h = h < 10 ? '0' + h : h
				m = m < 10 ? '0' + m : m
				s = s < 10 ? '0' + s : s
				return `${h}:${m}:${s}`
			}
		}
	}
</script>

<style>
	@import url("interviewer1.css");
</style>